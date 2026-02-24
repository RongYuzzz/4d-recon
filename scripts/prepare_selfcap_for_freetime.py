#!/usr/bin/env python3
"""
Prepare a SelfCap scene for FreeTimeGS-style training input.

Input (selfcap_root):
- optimized/intri.yml
- optimized/extri.yml
- pcds/000000.ply ...
- videos/<cam>.mp4 (optional, needed only when --extract_images)

Output (out_root):
- triangulation/points3d_frameXXXXXX.npy
- triangulation/colors_frameXXXXXX.npy
- triangulation/frame_manifest.csv
- colmap/images/<cam>/... (if --extract_images)
- colmap/sparse/0/{cameras.bin,images.bin,points3D.bin}
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import numpy as np


def _import_colmap_rw():
    repo_root = Path(__file__).resolve().parents[1]
    datasets_dir = repo_root / "third_party" / "FreeTimeGsVanilla" / "datasets"
    if not datasets_dir.exists():
        raise RuntimeError(f"Cannot find datasets dir: {datasets_dir}")
    if str(datasets_dir) not in sys.path:
        sys.path.insert(0, str(datasets_dir))
    from read_write_model import Camera, Image, Point3D, rotmat2qvec, write_model  # type: ignore

    return Camera, Image, Point3D, rotmat2qvec, write_model


def _parse_opencv_yaml_matrices(
    yaml_path: Path, require_names: bool = True
) -> tuple[dict[str, np.ndarray], list[str]]:
    text = yaml_path.read_text(encoding="utf-8")

    matrix_pat = re.compile(
        r"(?ms)^([A-Za-z0-9_]+):\s*!!opencv-matrix\s*"
        r"\n\s*rows:\s*(\d+)\s*"
        r"\n\s*cols:\s*(\d+)\s*"
        r"\n\s*dt:\s*[A-Za-z0-9]+\s*"
        r"\n\s*data:\s*\[([^\]]*)\]"
    )
    matrices: dict[str, np.ndarray] = {}
    for m in matrix_pat.finditer(text):
        key = m.group(1)
        rows = int(m.group(2))
        cols = int(m.group(3))
        values = np.fromstring(m.group(4), sep=",", dtype=np.float64)
        if values.size != rows * cols:
            raise ValueError(
                f"Bad matrix size for {key} in {yaml_path}: "
                f"expected {rows * cols}, got {values.size}"
            )
        matrices[key] = values.reshape(rows, cols)

    names = re.findall(r'(?m)^\s*-\s*"([^"]+)"\s*$', text)
    if not names:
        k_names = sorted(k[2:] for k in matrices if k.startswith("K_"))
        names = k_names

    if require_names and not names:
        raise ValueError(f"No camera names found in {yaml_path}")
    return matrices, names


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


def _read_binary_ply_xyz_rgb(ply_path: Path) -> tuple[np.ndarray, np.ndarray]:
    with ply_path.open("rb") as f:
        header_lines: list[str] = []
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"Invalid PLY: missing end_header ({ply_path})")
            line_s = line.decode("ascii", errors="strict").strip()
            header_lines.append(line_s)
            if line_s == "end_header":
                break
        data_offset = f.tell()

    if not header_lines or header_lines[0] != "ply":
        raise ValueError(f"Not a PLY file: {ply_path}")
    if "format binary_little_endian 1.0" not in header_lines:
        raise ValueError(f"Unsupported PLY format (need binary_little_endian): {ply_path}")

    vertex_count = None
    in_vertex = False
    props: list[tuple[str, str]] = []
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
                raise ValueError(f"Unsupported PLY property type '{ply_type}' in {ply_path}")
            props.append((prop_name, _PLY_DTYPES[ply_type]))

    if vertex_count is None:
        raise ValueError(f"No vertex element in {ply_path}")
    if not props:
        raise ValueError(f"No vertex properties in {ply_path}")

    dtype = np.dtype(props)
    with ply_path.open("rb") as f:
        f.seek(data_offset)
        arr = np.fromfile(f, dtype=dtype, count=vertex_count)

    for req in ("x", "y", "z"):
        if req not in arr.dtype.names:
            raise ValueError(f"Missing '{req}' in {ply_path}")

    xyz = np.stack([arr["x"], arr["y"], arr["z"]], axis=1).astype(np.float32, copy=False)

    if all(c in arr.dtype.names for c in ("red", "green", "blue")):
        rgb = np.stack([arr["red"], arr["green"], arr["blue"]], axis=1).astype(np.float32, copy=False)
    else:
        rgb = np.zeros_like(xyz, dtype=np.float32)

    return xyz, rgb


def _sample_points(
    xyz: np.ndarray,
    rgb: np.ndarray,
    max_points: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    if max_points > 0 and xyz.shape[0] > max_points:
        idx = rng.choice(xyz.shape[0], size=max_points, replace=False)
        return xyz[idx], rgb[idx]
    return xyz, rgb


def _ffprobe_size(video_path: Path, ffprobe_bin: str) -> tuple[int, int]:
    cmd = [
        ffprobe_bin,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(video_path),
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    if "x" not in out:
        raise RuntimeError(f"Cannot parse ffprobe size output: '{out}'")
    w_str, h_str = out.split("x", 1)
    return int(w_str), int(h_str)


def _extract_video_frames(
    video_path: Path,
    out_dir: Path,
    frame_start: int,
    frame_end: int,
    ffmpeg_bin: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    select_expr = f"select=between(n\\,{frame_start}\\,{frame_end - 1})"
    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        select_expr,
        "-vsync",
        "0",
        "-start_number",
        "0",
        str(out_dir / "%06d.jpg"),
    ]
    subprocess.run(cmd, check=True)


def _iter_selected_frames(frame_ids: Iterable[int], frame_start: int, frame_end: int) -> list[int]:
    return sorted([f for f in frame_ids if frame_start <= f < frame_end])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcap_root", required=True, help="SelfCap scene root (contains videos/ pcds/ optimized/)")
    ap.add_argument("--out_root", required=True, help="Output root for FreeTimeGS-style inputs")
    ap.add_argument("--frame_start", type=int, default=0, help="Inclusive source frame start")
    ap.add_argument("--frame_end", type=int, default=-1, help="Exclusive source frame end, -1 means auto to max+1")
    ap.add_argument("--max_triangulation_points", type=int, default=0, help="Per-frame point cap for triangulation")
    ap.add_argument("--max_colmap_points", type=int, default=200_000, help="Point cap for points3D.bin")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--keep_frame_index", action="store_true", help="Keep original frame index in output filenames")
    ap.add_argument("--extract_images", action="store_true", help="Extract selected frames from videos to colmap/images")
    ap.add_argument("--image_width", type=int, default=0, help="Override COLMAP camera width")
    ap.add_argument("--image_height", type=int, default=0, help="Override COLMAP camera height")
    ap.add_argument("--ffmpeg_bin", default="ffmpeg")
    ap.add_argument("--ffprobe_bin", default="ffprobe")
    args = ap.parse_args()

    selfcap_root = Path(args.selfcap_root)
    out_root = Path(args.out_root)

    intri_path = selfcap_root / "optimized" / "intri.yml"
    extri_path = selfcap_root / "optimized" / "extri.yml"
    pcd_dir = selfcap_root / "pcds"
    videos_dir = selfcap_root / "videos"
    if not intri_path.exists() or not extri_path.exists():
        raise FileNotFoundError(f"Missing optimized intrinsics/extrinsics under: {selfcap_root}")
    if not pcd_dir.exists():
        raise FileNotFoundError(f"Missing pcds directory: {pcd_dir}")

    intri_mats, camera_names = _parse_opencv_yaml_matrices(intri_path)
    extri_mats, _ = _parse_opencv_yaml_matrices(extri_path, require_names=False)

    pcd_files = sorted(pcd_dir.glob("*.ply"))
    if not pcd_files:
        raise ValueError(f"No PLY files found in {pcd_dir}")
    frame_to_pcd: dict[int, Path] = {}
    for p in pcd_files:
        if not p.stem.isdigit():
            continue
        frame_to_pcd[int(p.stem)] = p
    if not frame_to_pcd:
        raise ValueError(f"No numeric frame PLY files found in {pcd_dir}")

    min_frame = min(frame_to_pcd)
    max_frame = max(frame_to_pcd)
    frame_start = max(args.frame_start, min_frame)
    frame_end = (max_frame + 1) if args.frame_end < 0 else args.frame_end
    if frame_start >= frame_end:
        raise ValueError(
            f"Invalid frame range [{frame_start}, {frame_end}), available=[{min_frame}, {max_frame}]"
        )

    selected = _iter_selected_frames(frame_to_pcd.keys(), frame_start, frame_end)
    if not selected:
        raise ValueError(f"No frames selected in [{frame_start}, {frame_end})")

    tri_dir = out_root / "triangulation"
    tri_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    manifest_path = tri_dir / "frame_manifest.csv"

    first_xyz = first_rgb = None
    with manifest_path.open("w", encoding="utf-8", newline="") as mf:
        writer = csv.writer(mf)
        writer.writerow(["source_frame_idx", "output_frame_idx", "num_points", "source_ply"])
        for i, src_idx in enumerate(selected):
            out_idx = src_idx if args.keep_frame_index else i
            xyz, rgb = _read_binary_ply_xyz_rgb(frame_to_pcd[src_idx])
            xyz, rgb = _sample_points(xyz, rgb, args.max_triangulation_points, rng)

            np.save(tri_dir / f"points3d_frame{out_idx:06d}.npy", xyz.astype(np.float32, copy=False))
            np.save(tri_dir / f"colors_frame{out_idx:06d}.npy", rgb.astype(np.float32, copy=False))
            writer.writerow([src_idx, out_idx, int(xyz.shape[0]), frame_to_pcd[src_idx].name])

            if first_xyz is None:
                first_xyz = xyz
                first_rgb = rgb

    assert first_xyz is not None and first_rgb is not None
    colmap_xyz, colmap_rgb = _sample_points(first_xyz, first_rgb, args.max_colmap_points, rng)

    # COLMAP output
    colmap_dir = out_root / "colmap"
    images_dir = colmap_dir / "images"
    sparse_dir = colmap_dir / "sparse" / "0"
    images_dir.mkdir(parents=True, exist_ok=True)
    sparse_dir.mkdir(parents=True, exist_ok=True)

    # Always create camera folders to satisfy downstream folder discovery.
    for cam in camera_names:
        (images_dir / cam).mkdir(parents=True, exist_ok=True)

    if args.image_width > 0 and args.image_height > 0:
        width, height = args.image_width, args.image_height
    else:
        # Infer from first available video.
        width = height = 0
        for cam in camera_names:
            vp = videos_dir / f"{cam}.mp4"
            if vp.exists():
                width, height = _ffprobe_size(vp, args.ffprobe_bin)
                break
        if width <= 0 or height <= 0:
            raise ValueError(
                "Cannot infer image size. Provide --image_width/--image_height, "
                "or include videos/<cam>.mp4."
            )

    if args.extract_images:
        for cam in camera_names:
            video_path = videos_dir / f"{cam}.mp4"
            if not video_path.exists():
                raise FileNotFoundError(f"Missing video for camera {cam}: {video_path}")
            _extract_video_frames(
                video_path=video_path,
                out_dir=images_dir / cam,
                frame_start=frame_start,
                frame_end=frame_end,
                ffmpeg_bin=args.ffmpeg_bin,
            )

    Camera, Image, Point3D, rotmat2qvec, write_model = _import_colmap_rw()

    cameras = {}
    images = {}
    points3d = {}

    for i, cam in enumerate(camera_names):
        camera_id = i + 1
        k_key = f"K_{cam}"
        dist_key = f"dist_{cam}"
        rot_key = f"Rot_{cam}"
        t_key = f"T_{cam}"

        if k_key not in intri_mats:
            raise KeyError(f"Missing {k_key} in {intri_path}")
        if rot_key not in extri_mats or t_key not in extri_mats:
            raise KeyError(f"Missing {rot_key}/{t_key} in {extri_path}")

        k = intri_mats[k_key]
        fx = float(k[0, 0])
        fy = float(k[1, 1])
        cx = float(k[0, 2])
        cy = float(k[1, 2])
        dist = intri_mats.get(dist_key, np.zeros((1, 5), dtype=np.float64)).reshape(-1)
        if dist.size < 4:
            dist = np.pad(dist, (0, 4 - dist.size), mode="constant")

        if np.max(np.abs(dist[:4])) > 1e-12:
            model = "OPENCV"
            params = np.array([fx, fy, cx, cy, dist[0], dist[1], dist[2], dist[3]], dtype=np.float64)
        else:
            model = "PINHOLE"
            params = np.array([fx, fy, cx, cy], dtype=np.float64)

        cameras[camera_id] = Camera(
            id=camera_id,
            model=model,
            width=int(width),
            height=int(height),
            params=params,
        )

        rot = extri_mats[rot_key]
        tvec = extri_mats[t_key].reshape(3)
        qvec = rotmat2qvec(rot.astype(np.float64))

        images[camera_id] = Image(
            id=camera_id,
            qvec=np.asarray(qvec, dtype=np.float64),
            tvec=np.asarray(tvec, dtype=np.float64),
            camera_id=camera_id,
            name=f"{cam}.jpg",
            xys=np.empty((0, 2), dtype=np.float64),
            point3D_ids=np.empty((0,), dtype=np.int64),
        )

    for i in range(colmap_xyz.shape[0]):
        point_id = i + 1
        points3d[point_id] = Point3D(
            id=point_id,
            xyz=np.asarray(colmap_xyz[i], dtype=np.float64),
            rgb=np.asarray(np.clip(colmap_rgb[i], 0, 255), dtype=np.uint8),
            error=1.0,
            image_ids=np.empty((0,), dtype=np.int32),
            point2D_idxs=np.empty((0,), dtype=np.int32),
        )

    write_model(cameras, images, points3d, str(sparse_dir), ext=".bin")

    print(f"[Info] selfcap_root: {selfcap_root}")
    print(f"[Info] out_root: {out_root}")
    print(f"[Info] selected_frames: {len(selected)} [{selected[0]}, {selected[-1]}]")
    print(f"[Info] triangulation_dir: {tri_dir}")
    print(f"[Info] colmap_sparse: {sparse_dir}")
    print(f"[Info] cameras: {len(cameras)} points3D: {len(points3d)}")
    print(f"[Info] image_size: {width}x{height}")
    print(f"[Info] extract_images: {args.extract_images}")


if __name__ == "__main__":
    main()
