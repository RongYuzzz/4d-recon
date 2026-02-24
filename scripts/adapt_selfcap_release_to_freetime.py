#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import BinaryIO

import numpy as np

_OPENCV_MATRIX_PATTERN = re.compile(
    r"(?ms)^([A-Za-z0-9_]+):\s*!!opencv-matrix\s*"
    r"\n\s*rows:\s*(\d+)\s*"
    r"\n\s*cols:\s*(\d+)\s*"
    r"\n\s*dt:\s*[A-Za-z0-9]+\s*"
    r"\n\s*data:\s*\[([^\]]*)\]"
)

_PLY_DTYPES = {
    "char": "i1",
    "uchar": "u1",
    "short": "<i2",
    "ushort": "<u2",
    "int": "<i4",
    "uint": "<u4",
    "float": "<f4",
    "double": "<f8",
}


def parse_opencv_yml_mats(text: str) -> dict[str, np.ndarray]:
    mats: dict[str, np.ndarray] = {}
    for match in _OPENCV_MATRIX_PATTERN.finditer(text):
        key = match.group(1)
        rows = int(match.group(2))
        cols = int(match.group(3))
        values = np.fromstring(match.group(4), sep=",", dtype=np.float64)
        if values.size != rows * cols:
            raise ValueError(
                f"Matrix {key} has bad size: expected {rows * cols}, got {values.size}"
            )
        mats[key] = values.reshape(rows, cols)
    if not mats:
        raise ValueError("No !!opencv-matrix entries found")
    return mats


def read_binary_ply_xyz_rgb(fobj: BinaryIO) -> tuple[np.ndarray, np.ndarray]:
    header_lines: list[str] = []
    while True:
        line = fobj.readline()
        if not line:
            raise ValueError("Invalid PLY: missing end_header")
        line_s = line.decode("ascii", errors="strict").strip()
        header_lines.append(line_s)
        if line_s == "end_header":
            break

    if not header_lines or header_lines[0] != "ply":
        raise ValueError("Invalid PLY header")
    if "format binary_little_endian 1.0" not in header_lines:
        raise ValueError("Only binary_little_endian PLY is supported")

    vertex_count: int | None = None
    in_vertex = False
    properties: list[tuple[str, str]] = []
    for ln in header_lines:
        toks = ln.split()
        if len(toks) >= 3 and toks[0] == "element":
            in_vertex = toks[1] == "vertex"
            if in_vertex:
                vertex_count = int(toks[2])
            continue
        if in_vertex and len(toks) == 3 and toks[0] == "property":
            ply_type = toks[1]
            prop_name = toks[2]
            if ply_type not in _PLY_DTYPES:
                raise ValueError(f"Unsupported PLY type: {ply_type}")
            properties.append((prop_name, _PLY_DTYPES[ply_type]))

    if vertex_count is None:
        raise ValueError("PLY vertex count missing")
    if not properties:
        raise ValueError("PLY vertex properties missing")

    dtype = np.dtype(properties)
    payload_size = dtype.itemsize * vertex_count
    payload = fobj.read(payload_size)
    if len(payload) != payload_size:
        raise ValueError(
            f"PLY payload truncated: expected {payload_size} bytes, got {len(payload)}"
        )
    arr = np.frombuffer(payload, dtype=dtype, count=vertex_count)

    for name in ("x", "y", "z", "red", "green", "blue"):
        if name not in arr.dtype.names:
            raise ValueError(f"PLY missing required property: {name}")

    xyz = np.stack([arr["x"], arr["y"], arr["z"]], axis=1).astype(np.float32, copy=False)
    rgb = np.stack([arr["red"], arr["green"], arr["blue"]], axis=1).astype(
        np.float32, copy=False
    )
    return xyz, rgb


def _import_colmap_rw():
    repo_root = Path(__file__).resolve().parents[1]
    datasets_dir = repo_root / "third_party" / "FreeTimeGsVanilla" / "datasets"
    if not datasets_dir.exists():
        raise RuntimeError(f"Cannot find COLMAP writer dir: {datasets_dir}")
    if str(datasets_dir) not in sys.path:
        sys.path.insert(0, str(datasets_dir))
    from read_write_model import Camera, Image, Point3D, rotmat2qvec, write_model  # type: ignore

    return Camera, Image, Point3D, rotmat2qvec, write_model


def write_colmap_sparse0(
    out_sparse_dir: Path,
    camera_ids: list[str],
    intrinsics: dict[str, np.ndarray],
    rotations: dict[str, np.ndarray],
    translations: dict[str, np.ndarray],
    points_xyz: np.ndarray,
    points_rgb: np.ndarray,
    image_width: int,
    image_height: int,
    image_downscale: int = 1,
) -> None:
    if image_downscale <= 0:
        raise ValueError("image_downscale must be >= 1")
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image_width/image_height must be positive")

    Camera, Image, Point3D, rotmat2qvec, write_model = _import_colmap_rw()
    out_sparse_dir.mkdir(parents=True, exist_ok=True)

    cameras = {}
    images = {}
    points3D = {}

    for i, cam in enumerate(camera_ids):
        camera_id = i + 1
        k_key = f"K_{cam}"
        rot_key = f"Rot_{cam}"
        t_key = f"T_{cam}"
        if k_key not in intrinsics:
            raise KeyError(f"Missing {k_key}")
        if rot_key not in rotations:
            raise KeyError(f"Missing {rot_key}")
        if t_key not in translations:
            raise KeyError(f"Missing {t_key}")

        K = intrinsics[k_key]
        fx = float(K[0, 0]) / image_downscale
        fy = float(K[1, 1]) / image_downscale
        cx = float(K[0, 2]) / image_downscale
        cy = float(K[1, 2]) / image_downscale

        cameras[camera_id] = Camera(
            id=camera_id,
            model="PINHOLE",
            width=int(image_width),
            height=int(image_height),
            params=np.array([fx, fy, cx, cy], dtype=np.float64),
        )

        R = rotations[rot_key].reshape(3, 3).astype(np.float64)
        T = translations[t_key].reshape(3).astype(np.float64)
        qvec = np.asarray(rotmat2qvec(R), dtype=np.float64)

        images[camera_id] = Image(
            id=camera_id,
            qvec=qvec,
            tvec=T,
            camera_id=camera_id,
            name=f"{cam}.jpg",
            xys=np.empty((0, 2), dtype=np.float64),
            point3D_ids=np.empty((0,), dtype=np.int64),
        )

    for i in range(points_xyz.shape[0]):
        point_id = i + 1
        points3D[point_id] = Point3D(
            id=point_id,
            xyz=np.asarray(points_xyz[i], dtype=np.float64),
            rgb=np.asarray(np.clip(points_rgb[i], 0, 255), dtype=np.uint8),
            error=1.0,
            image_ids=np.empty((0,), dtype=np.int32),
            point2D_idxs=np.empty((0,), dtype=np.int32),
        )

    write_model(cameras, images, points3D, str(out_sparse_dir), ext=".bin")


def extract_video_frames(
    video_path: Path,
    out_dir: Path,
    frame_start: int,
    num_frames: int,
    downscale: int,
) -> tuple[int, int]:
    try:
        import cv2  # type: ignore
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Missing dependency: cv2. Install with `python -m pip install opencv-python` "
            "to enable video frame extraction."
        ) from exc

    if frame_start < 0:
        raise ValueError("frame_start must be >= 0")
    if num_frames <= 0:
        raise ValueError("num_frames must be > 0")
    if downscale <= 0:
        raise ValueError("downscale must be >= 1")

    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    saved = 0
    src_idx = 0
    out_w: int | None = None
    out_h: int | None = None
    try:
        while saved < num_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if src_idx >= frame_start:
                if downscale > 1:
                    h, w = frame.shape[:2]
                    frame = cv2.resize(
                        frame,
                        (max(1, w // downscale), max(1, h // downscale)),
                        interpolation=cv2.INTER_AREA,
                    )
                if out_w is None or out_h is None:
                    out_h, out_w = frame.shape[:2]
                out_path = out_dir / f"{saved:06d}.jpg"
                ok_write = cv2.imwrite(str(out_path), frame)
                if not ok_write:
                    raise RuntimeError(f"Failed to write frame: {out_path}")
                saved += 1
            src_idx += 1
    finally:
        cap.release()

    if saved != num_frames:
        raise RuntimeError(
            f"Video {video_path} only yielded {saved} frames "
            f"from frame_start={frame_start}, expected {num_frames}"
        )
    assert out_w is not None and out_h is not None
    return out_w, out_h


def _read_tar_text(tf: tarfile.TarFile, member_name: str) -> str:
    fobj = tf.extractfile(member_name)
    if fobj is None:
        raise FileNotFoundError(f"Missing tar member: {member_name}")
    return fobj.read().decode("utf-8")


def _extract_tar_member_to_tempfile(
    tf: tarfile.TarFile, member_name: str, suffix: str
) -> Path:
    fobj = tf.extractfile(member_name)
    if fobj is None:
        raise FileNotFoundError(f"Missing tar member: {member_name}")
    tmp = tempfile.NamedTemporaryFile(prefix="selfcap_", suffix=suffix, delete=False)
    tmp_path = Path(tmp.name)
    try:
        shutil.copyfileobj(fobj, tmp)
    finally:
        tmp.close()
    return tmp_path


def _sample_points(
    xyz: np.ndarray, rgb: np.ndarray, max_points: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    if max_points > 0 and xyz.shape[0] > max_points:
        idx = rng.choice(xyz.shape[0], size=max_points, replace=False)
        return xyz[idx], rgb[idx]
    return xyz, rgb


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Adapt SelfCap bar-release.tar.gz to FreeTimeGS Gate-1 input",
    )
    ap.add_argument("--tar_gz", required=True, help="Path to bar-release.tar.gz")
    ap.add_argument("--output_dir", required=True, help="Output dataset directory")
    ap.add_argument(
        "--camera_ids",
        default="02,03,04,05,06,07,08,09",
        help="Comma-separated camera IDs, e.g. 02,03,04",
    )
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--num_frames", type=int, default=60)
    ap.add_argument("--image_downscale", type=int, default=2)
    ap.add_argument("--max_points", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tar_path = Path(args.tar_gz)
    out_root = Path(args.output_dir)
    if args.frame_start < 0:
        raise ValueError("--frame_start must be >= 0")
    if args.num_frames <= 0:
        raise ValueError("--num_frames must be > 0")
    if args.image_downscale <= 0:
        raise ValueError("--image_downscale must be >= 1")
    if not tar_path.exists():
        raise FileNotFoundError(f"Tarball not found: {tar_path}")

    camera_ids = [c.strip() for c in args.camera_ids.split(",") if c.strip()]
    if not camera_ids:
        raise ValueError("--camera_ids is empty")

    images_dir = out_root / "images"
    sparse0_dir = out_root / "sparse" / "0"
    tri_dir = out_root / "triangulation"
    images_dir.mkdir(parents=True, exist_ok=True)
    sparse0_dir.mkdir(parents=True, exist_ok=True)
    tri_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    intrinsics: dict[str, np.ndarray]
    extrinsics: dict[str, np.ndarray]

    first_frame_xyz: np.ndarray | None = None
    first_frame_rgb: np.ndarray | None = None
    image_width: int | None = None
    image_height: int | None = None

    with tarfile.open(tar_path, "r:gz") as tf:
        intrinsics = parse_opencv_yml_mats(_read_tar_text(tf, "bar-release/optimized/intri.yml"))
        extrinsics = parse_opencv_yml_mats(_read_tar_text(tf, "bar-release/optimized/extri.yml"))

        for cam in camera_ids:
            video_member = f"bar-release/videos/{cam}.mp4"
            tmp_video = _extract_tar_member_to_tempfile(tf, video_member, suffix=f"_{cam}.mp4")
            try:
                w, h = extract_video_frames(
                    video_path=tmp_video,
                    out_dir=images_dir / cam,
                    frame_start=args.frame_start,
                    num_frames=args.num_frames,
                    downscale=args.image_downscale,
                )
            finally:
                try:
                    os.unlink(tmp_video)
                except OSError:
                    pass
            if image_width is None and image_height is None:
                image_width, image_height = w, h

        manifest_path = tri_dir / "frame_manifest.csv"
        with manifest_path.open("w", newline="", encoding="utf-8") as mf:
            writer = csv.writer(mf)
            writer.writerow(["source_frame_idx", "output_frame_idx", "num_points", "source_ply"])

            for out_idx in range(args.num_frames):
                src_idx = args.frame_start + out_idx
                ply_member = f"bar-release/pcds/{src_idx:06d}.ply"
                ply_fobj = tf.extractfile(ply_member)
                if ply_fobj is None:
                    raise FileNotFoundError(f"Missing tar member: {ply_member}")
                xyz, rgb = read_binary_ply_xyz_rgb(ply_fobj)
                xyz, rgb = _sample_points(xyz, rgb, args.max_points, rng)
                np.save(tri_dir / f"points3d_frame{out_idx:06d}.npy", xyz.astype(np.float32))
                np.save(tri_dir / f"colors_frame{out_idx:06d}.npy", rgb.astype(np.float32))
                writer.writerow([src_idx, out_idx, int(xyz.shape[0]), ply_member])
                if first_frame_xyz is None and xyz.shape[0] > 0:
                    first_frame_xyz = xyz
                    first_frame_rgb = rgb

    if first_frame_xyz is None or first_frame_rgb is None:
        raise ValueError("Selected frame range has no valid points for sparse/0 points3D")
    if image_width is None or image_height is None:
        raise ValueError("No video frames extracted")

    sparse_xyz, sparse_rgb = _sample_points(
        first_frame_xyz, first_frame_rgb, max_points=20000, rng=rng
    )
    write_colmap_sparse0(
        out_sparse_dir=sparse0_dir,
        camera_ids=camera_ids,
        intrinsics=intrinsics,
        rotations=extrinsics,
        translations=extrinsics,
        points_xyz=sparse_xyz,
        points_rgb=sparse_rgb,
        image_width=image_width,
        image_height=image_height,
        image_downscale=args.image_downscale,
    )

    print(f"[Info] tar_gz: {tar_path}")
    print(f"[Info] output_dir: {out_root}")
    print(f"[Info] camera_ids: {','.join(camera_ids)}")
    print(f"[Info] frame_range: [{args.frame_start}, {args.frame_start + args.num_frames})")
    print(f"[Info] images_dir: {images_dir}")
    print(f"[Info] sparse0_dir: {sparse0_dir}")
    print(f"[Info] triangulation_dir: {tri_dir}")
    print(f"[Info] image_size: {image_width}x{image_height} downscale={args.image_downscale}")
    print(f"[Info] sparse_points3D: {sparse_xyz.shape[0]}")


if __name__ == "__main__":
    main()
