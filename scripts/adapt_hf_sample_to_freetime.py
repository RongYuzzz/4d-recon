#!/usr/bin/env python3
"""
Adapt a HuggingFace-style COLMAP sample into FreeTime-compatible layout.

Input layout (source_dir):
  - images/                  # flat or nested image files referenced by COLMAP
  - sparse/0/{cameras,images,points3D}.bin|.txt

Output layout (output_dir):
  - images/<camera_folder>/<frame>.jpg|png
  - sparse/0/{cameras,images,points3D}.bin
  - adapt_manifest.csv
  - triangulation/*.npy (optional, controlled by --triangulation_mode)
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class SelectedImage:
    image_id: int
    image_name: str
    camera_folder: str
    source_path: Path


def load_rw_module(repo_root: Path):
    rw_path = repo_root / "third_party" / "FreeTimeGsVanilla" / "datasets" / "read_write_model.py"
    spec = importlib.util.spec_from_file_location("read_write_model", rw_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load read_write_model.py from: {rw_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def detect_model_ext(sparse_dir: Path) -> str:
    if (sparse_dir / "cameras.bin").exists():
        return ".bin"
    if (sparse_dir / "cameras.txt").exists():
        return ".txt"
    raise FileNotFoundError(f"No COLMAP model found in: {sparse_dir}")


def camera_folder_from_image_name(image_name: str) -> str:
    norm = image_name.replace("\\", "/")
    p = Path(norm)
    if len(p.parts) > 1:
        return p.parent.name
    return p.stem


def build_image_index(images_root: Path) -> Dict[str, List[Path]]:
    by_basename: Dict[str, List[Path]] = {}
    for path in images_root.rglob("*"):
        if not path.is_file():
            continue
        by_basename.setdefault(path.name, []).append(path)
    return by_basename


def resolve_source_image(images_root: Path, image_name: str, by_basename: Dict[str, List[Path]]) -> Optional[Path]:
    norm = image_name.replace("\\", "/")
    direct = images_root / norm
    if direct.exists() and direct.is_file():
        return direct

    candidates = by_basename.get(Path(norm).name, [])
    if len(candidates) == 1:
        return candidates[0]
    return None


def select_images(
    images: Dict[int, object],
    images_root: Path,
    max_cameras: int,
) -> List[SelectedImage]:
    by_basename = build_image_index(images_root)
    by_folder: Dict[str, SelectedImage] = {}
    for image_id, image in sorted(images.items(), key=lambda kv: str(kv[1].name)):
        src = resolve_source_image(images_root, image.name, by_basename)
        if src is None:
            continue
        folder = camera_folder_from_image_name(image.name)
        candidate = SelectedImage(
            image_id=int(image_id),
            image_name=str(image.name),
            camera_folder=folder,
            source_path=src,
        )
        # Keep one representative image per camera folder.
        current = by_folder.get(folder)
        if current is None or candidate.image_name < current.image_name:
            by_folder[folder] = candidate

    selected = sorted(by_folder.values(), key=lambda x: (x.camera_folder, x.image_name))
    if max_cameras > 0:
        selected = selected[:max_cameras]
    return selected


def choose_output_extension(selected: Iterable[SelectedImage]) -> str:
    exts = sorted({item.source_path.suffix.lower() for item in selected})
    if not exts:
        raise ValueError("No selected images.")
    if len(exts) != 1:
        raise ValueError(f"Mixed source extensions are not supported: {exts}")
    return exts[0]


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def materialize(src: Path, dst: Path, mode: str) -> None:
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if mode == "symlink":
        os.symlink(src, dst)
        return
    if mode == "hardlink":
        os.link(src, dst)
        return
    if mode == "copy":
        shutil.copy2(src, dst)
        return
    raise ValueError(f"Unsupported copy mode: {mode}")


def filter_model(
    rw,
    cameras: Dict[int, object],
    images: Dict[int, object],
    points3d: Dict[int, object],
    selected: List[SelectedImage],
) -> Tuple[Dict[int, object], Dict[int, object], Dict[int, object]]:
    keep_image_ids = {item.image_id for item in selected}
    keep_images = {iid: images[iid] for iid in keep_image_ids}
    keep_camera_ids = {int(img.camera_id) for img in keep_images.values()}
    keep_cameras = {cid: cameras[cid] for cid in keep_camera_ids}

    Point3D = rw.Point3D
    Image = rw.Image

    keep_points: Dict[int, object] = {}
    keep_image_id_array = np.array(sorted(keep_image_ids), dtype=np.int32)

    for point_id, point in points3d.items():
        mask = np.isin(point.image_ids.astype(np.int32), keep_image_id_array)
        if int(mask.sum()) == 0:
            continue
        keep_points[int(point_id)] = Point3D(
            id=int(point.id),
            xyz=point.xyz.astype(np.float64),
            rgb=point.rgb.astype(np.uint8),
            error=float(point.error),
            image_ids=point.image_ids[mask].astype(np.int32),
            point2D_idxs=point.point2D_idxs[mask].astype(np.int32),
        )

    keep_point_ids = np.array(sorted(keep_points.keys()), dtype=np.int64)
    rewritten_images: Dict[int, object] = {}
    for image_id, image in keep_images.items():
        point_ids = image.point3D_ids.astype(np.int64).copy()
        valid = np.isin(point_ids, keep_point_ids)
        point_ids[~valid] = -1
        rewritten_images[int(image_id)] = Image(
            id=int(image.id),
            qvec=image.qvec.astype(np.float64),
            tvec=image.tvec.astype(np.float64),
            camera_id=int(image.camera_id),
            name=str(image.name),
            xys=image.xys.astype(np.float64),
            point3D_ids=point_ids,
        )

    return keep_cameras, rewritten_images, keep_points


def write_manifest(path: Path, rows: List[SelectedImage]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "image_name", "camera_folder", "source_path"])
        for row in rows:
            writer.writerow([row.image_id, row.image_name, row.camera_folder, str(row.source_path)])


def build_output_frames(
    output_images_root: Path,
    selected: List[SelectedImage],
    num_frames: int,
    frame_digits: int,
    output_ext: str,
    copy_mode: str,
) -> None:
    for item in selected:
        cam_dir = output_images_root / item.camera_folder
        cam_dir.mkdir(parents=True, exist_ok=True)
        for frame_idx in range(num_frames):
            frame_name = f"{frame_idx:0{frame_digits}d}{output_ext}"
            dst = cam_dir / frame_name
            materialize(item.source_path, dst, mode=copy_mode)


def points_dict_to_arrays(
    points3d: Dict[int, object],
    max_points: int,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    if not points3d:
        return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.float32)

    point_ids = np.array(sorted(points3d.keys()), dtype=np.int64)
    if max_points > 0 and len(point_ids) > max_points:
        point_ids = rng.choice(point_ids, size=max_points, replace=False)

    xyz_list: List[np.ndarray] = []
    rgb_list: List[np.ndarray] = []
    for point_id in point_ids:
        p = points3d[int(point_id)]
        xyz_list.append(np.asarray(p.xyz, dtype=np.float32))
        rgb_list.append(np.asarray(p.rgb, dtype=np.float32))
    xyz = np.stack(xyz_list, axis=0) if xyz_list else np.zeros((0, 3), dtype=np.float32)
    rgb = np.stack(rgb_list, axis=0) if rgb_list else np.zeros((0, 3), dtype=np.float32)
    return xyz, rgb


def write_triangulation_manifest(path: Path, rows: List[Tuple[int, int, int, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_idx", "source_frame", "num_points", "mode"])
        writer.writerows(rows)


def export_static_repeat_triangulation(
    out_dir: Path,
    points3d: Dict[int, object],
    num_frames: int,
    max_points: int,
    seed: int,
) -> Tuple[int, int]:
    if num_frames <= 0:
        raise ValueError("triangulation_num_frames must be > 0 for static_repeat mode")
    rng = np.random.default_rng(seed)
    xyz, rgb = points_dict_to_arrays(points3d, max_points=max_points, rng=rng)
    if xyz.shape[0] == 0:
        raise ValueError("static_repeat mode has zero points after filtering")

    ensure_clean_dir(out_dir)
    rows: List[Tuple[int, int, int, str]] = []
    for frame_idx in range(num_frames):
        np.save(out_dir / f"points3d_frame{frame_idx:06d}.npy", xyz)
        np.save(out_dir / f"colors_frame{frame_idx:06d}.npy", rgb)
        rows.append((frame_idx, -1, int(xyz.shape[0]), "static_repeat"))
    write_triangulation_manifest(out_dir / "frame_manifest.csv", rows)
    return num_frames, int(xyz.shape[0])


def resolve_points3d_path(frame_dir: Path) -> Optional[Path]:
    candidates = [
        frame_dir / "points3D.bin",
        frame_dir / "points3D.txt",
        frame_dir / "sparse" / "0" / "points3D.bin",
        frame_dir / "sparse" / "0" / "points3D.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def collect_frame_sparse_dirs(per_frame_sparse_dir: Path) -> List[Tuple[int, Path]]:
    pattern = re.compile(r"^frame_(\d+)$")
    frame_dirs: List[Tuple[int, Path]] = []
    for child in per_frame_sparse_dir.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if not match:
            continue
        frame_idx = int(match.group(1))
        frame_dirs.append((frame_idx, child))
    frame_dirs.sort(key=lambda x: x[0])
    return frame_dirs


def read_points3d_file(rw, points_path: Path) -> Dict[int, object]:
    if points_path.suffix == ".bin":
        return rw.read_points3D_binary(str(points_path))
    if points_path.suffix == ".txt":
        return rw.read_points3D_text(str(points_path))
    raise ValueError(f"Unsupported points3D file extension: {points_path}")


def export_per_frame_sparse_triangulation(
    rw,
    out_dir: Path,
    per_frame_sparse_dir: Path,
    frame_start: int,
    frame_end: int,
    max_points: int,
    seed: int,
) -> Tuple[int, int]:
    if not per_frame_sparse_dir.exists():
        raise FileNotFoundError(f"per_frame_sparse_dir does not exist: {per_frame_sparse_dir}")
    frame_dirs_all = collect_frame_sparse_dirs(per_frame_sparse_dir)
    if not frame_dirs_all:
        raise ValueError(f"No frame_XXXXXX directories found under: {per_frame_sparse_dir}")

    selected: List[Tuple[int, Path]] = []
    for src_frame_idx, frame_dir in frame_dirs_all:
        if src_frame_idx < frame_start:
            continue
        if frame_end >= 0 and src_frame_idx >= frame_end:
            continue
        selected.append((src_frame_idx, frame_dir))
    if not selected:
        raise ValueError(
            f"No per-frame sparse directories in requested range [{frame_start}, "
            f"{'end' if frame_end < 0 else frame_end})"
        )

    ensure_clean_dir(out_dir)
    rng = np.random.default_rng(seed)
    rows: List[Tuple[int, int, int, str]] = []
    max_points_seen = 0
    total_points = 0

    for out_frame_idx, (src_frame_idx, frame_dir) in enumerate(selected):
        points_path = resolve_points3d_path(frame_dir)
        if points_path is None:
            xyz = np.zeros((0, 3), dtype=np.float32)
            rgb = np.zeros((0, 3), dtype=np.float32)
        else:
            points = read_points3d_file(rw, points_path)
            xyz, rgb = points_dict_to_arrays(points, max_points=max_points, rng=rng)
        np.save(out_dir / f"points3d_frame{out_frame_idx:06d}.npy", xyz)
        np.save(out_dir / f"colors_frame{out_frame_idx:06d}.npy", rgb)
        rows.append((out_frame_idx, src_frame_idx, int(xyz.shape[0]), "per_frame_sparse"))
        max_points_seen = max(max_points_seen, int(xyz.shape[0]))
        total_points += int(xyz.shape[0])

    if total_points == 0:
        shutil.rmtree(out_dir, ignore_errors=True)
        raise ValueError("All selected per-frame sparse frames have zero points; aborting triangulation export.")

    write_triangulation_manifest(out_dir / "frame_manifest.csv", rows)
    return len(rows), max_points_seen


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source_dir", required=True, help="Input sample root with images/ and sparse/0")
    ap.add_argument("--output_dir", required=True, help="Output FreeTime-compatible root")
    ap.add_argument("--num_frames", type=int, default=24, help="Generated frames per camera folder")
    ap.add_argument("--frame_digits", type=int, default=6, help="Frame filename width")
    ap.add_argument("--max_cameras", type=int, default=0, help="0 means all available cameras")
    ap.add_argument(
        "--copy_mode",
        choices=["symlink", "hardlink", "copy"],
        default="symlink",
        help="How to materialize per-frame images",
    )
    ap.add_argument(
        "--triangulation_mode",
        choices=["none", "static_repeat", "per_frame_sparse"],
        default="none",
        help="How to generate triangulation/*.npy output",
    )
    ap.add_argument(
        "--triangulation_out_dir",
        default="",
        help="Triangulation output dir (default: <output_dir>/triangulation)",
    )
    ap.add_argument(
        "--triangulation_num_frames",
        type=int,
        default=-1,
        help="Used by static_repeat mode. -1 means reuse --num_frames",
    )
    ap.add_argument(
        "--per_frame_sparse_dir",
        default="",
        help="Used by per_frame_sparse mode. Default: <source_dir>/sparse",
    )
    ap.add_argument(
        "--triangulation_frame_start",
        type=int,
        default=0,
        help="Used by per_frame_sparse mode (inclusive source frame index)",
    )
    ap.add_argument(
        "--triangulation_frame_end",
        type=int,
        default=-1,
        help="Used by per_frame_sparse mode (exclusive source frame index, -1 for no upper bound)",
    )
    ap.add_argument(
        "--max_points",
        type=int,
        default=200000,
        help="Max points per triangulation frame. <=0 means keep all",
    )
    ap.add_argument("--seed", type=int, default=0)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    repo_root = Path(__file__).resolve().parents[1]
    rw = load_rw_module(repo_root)

    source_images = source_dir / "images"
    source_sparse = source_dir / "sparse" / "0"
    if not source_images.exists():
        raise FileNotFoundError(f"images directory not found: {source_images}")
    if not source_sparse.exists():
        raise FileNotFoundError(f"sparse/0 directory not found: {source_sparse}")
    if args.num_frames <= 0:
        raise ValueError("--num_frames must be > 0")

    model_ext = detect_model_ext(source_sparse)
    cameras, images, points3d = rw.read_model(str(source_sparse), ext=model_ext)
    selected = select_images(images, source_images, max_cameras=args.max_cameras)
    if not selected:
        raise ValueError(
            "No COLMAP images can be resolved from source images directory. "
            "Check that source images are downloaded and filenames match images.bin."
        )

    output_ext = choose_output_extension(selected)
    keep_cameras, keep_images, keep_points = filter_model(rw, cameras, images, points3d, selected)

    output_images = output_dir / "images"
    output_sparse = output_dir / "sparse" / "0"
    ensure_clean_dir(output_images)
    ensure_clean_dir(output_sparse)

    build_output_frames(
        output_images_root=output_images,
        selected=selected,
        num_frames=args.num_frames,
        frame_digits=args.frame_digits,
        output_ext=output_ext,
        copy_mode=args.copy_mode,
    )
    rw.write_model(keep_cameras, keep_images, keep_points, str(output_sparse), ext=".bin")
    write_manifest(output_dir / "adapt_manifest.csv", selected)

    tri_mode = args.triangulation_mode
    tri_out_dir = Path(args.triangulation_out_dir).resolve() if args.triangulation_out_dir else (output_dir / "triangulation")
    tri_frames = 0
    tri_max_points = 0
    tri_cleaned = False
    if tri_mode == "static_repeat":
        tri_num_frames = args.num_frames if args.triangulation_num_frames < 0 else args.triangulation_num_frames
        tri_frames, tri_max_points = export_static_repeat_triangulation(
            out_dir=tri_out_dir,
            points3d=keep_points,
            num_frames=tri_num_frames,
            max_points=args.max_points,
            seed=args.seed,
        )
    elif tri_mode == "per_frame_sparse":
        per_frame_sparse_dir = Path(args.per_frame_sparse_dir).resolve() if args.per_frame_sparse_dir else (source_dir / "sparse")
        tri_frames, tri_max_points = export_per_frame_sparse_triangulation(
            rw=rw,
            out_dir=tri_out_dir,
            per_frame_sparse_dir=per_frame_sparse_dir,
            frame_start=args.triangulation_frame_start,
            frame_end=args.triangulation_frame_end,
            max_points=args.max_points,
            seed=args.seed,
        )
    elif tri_mode == "none":
        if tri_out_dir.exists():
            shutil.rmtree(tri_out_dir)
            tri_cleaned = True

    print("=== Adapt Complete ===")
    print(f"source_dir: {source_dir}")
    print(f"output_dir: {output_dir}")
    print(f"selected cameras: {len(selected)}")
    print(f"generated frames/camera: {args.num_frames}")
    print(f"image extension: {output_ext}")
    print(f"copy mode: {args.copy_mode}")
    print(f"filtered sparse images: {len(keep_images)}")
    print(f"filtered sparse points3D: {len(keep_points)}")
    print(f"manifest: {output_dir / 'adapt_manifest.csv'}")
    print(f"triangulation_mode: {tri_mode}")
    if tri_mode != "none":
        print(f"triangulation_out_dir: {tri_out_dir}")
        print(f"triangulation_frames: {tri_frames}")
        print(f"triangulation_max_points: {tri_max_points}")
    elif tri_cleaned:
        print(f"triangulation_out_dir_removed: {tri_out_dir}")


if __name__ == "__main__":
    main()
