#!/usr/bin/env python3
"""
从 COLMAP sparse 导出 FreeTimeGS 所需的逐帧输入：
- points3d_frameXXXXXX.npy
- colors_frameXXXXXX.npy

支持两种模式：
1) visible_per_frame: 每帧聚合同时刻多相机可见点
2) static_copy: 每帧直接复制全局 points3D（Gate-0 烟雾测试）
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


FRAME_PATTERNS = (
    re.compile(r"frame[_-]?(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)(?=\.[^.]+$)"),
)


@dataclass(frozen=True)
class ImageRecord:
    image_id: int
    name: str
    point3d_ids: np.ndarray


def _import_read_write_model():
    repo_root = Path(__file__).resolve().parents[1]
    datasets_dir = repo_root / "third_party" / "FreeTimeGsVanilla" / "datasets"
    if not datasets_dir.exists():
        raise RuntimeError(
            "Cannot find read_write_model.py fallback. "
            f"Expected: {datasets_dir}"
        )
    if str(datasets_dir) not in sys.path:
        sys.path.insert(0, str(datasets_dir))
    from read_write_model import read_model  # type: ignore

    return read_model


def _load_with_pycolmap(sparse_dir: Path) -> tuple[list[ImageRecord], dict[int, tuple[np.ndarray, np.ndarray]], str]:
    try:
        import pycolmap  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise ImportError(str(exc)) from exc

    try:
        rec = pycolmap.Reconstruction()
        rec.read(str(sparse_dir))
    except TypeError:
        rec = pycolmap.Reconstruction(str(sparse_dir))

    if not rec.images:
        raise ValueError(f"No images in reconstruction: {sparse_dir}")
    if not rec.points3D:
        raise ValueError(f"No points3D in reconstruction: {sparse_dir}")

    points = {}
    for pid, p3d in rec.points3D.items():
        points[int(pid)] = (
            np.asarray(p3d.xyz, dtype=np.float32),
            np.asarray(p3d.color, dtype=np.float32),
        )

    images: list[ImageRecord] = []
    for image_id, img in rec.images.items():
        pids = []
        for p2d in img.points2D:
            pid = int(getattr(p2d, "point3D_id", -1))
            if pid != -1 and pid in points:
                pids.append(pid)
        images.append(
            ImageRecord(
                image_id=int(image_id),
                name=str(img.name),
                point3d_ids=np.asarray(pids, dtype=np.int64),
            )
        )

    return images, points, "pycolmap"


def _load_with_rw_model(sparse_dir: Path) -> tuple[list[ImageRecord], dict[int, tuple[np.ndarray, np.ndarray]], str]:
    read_model = _import_read_write_model()
    _, images_dict, points3d_dict = read_model(str(sparse_dir), ext=".bin")
    if not images_dict:
        raise ValueError(f"No images in reconstruction: {sparse_dir}")
    if not points3d_dict:
        raise ValueError(f"No points3D in reconstruction: {sparse_dir}")

    points = {}
    for pid, p3d in points3d_dict.items():
        points[int(pid)] = (
            np.asarray(p3d.xyz, dtype=np.float32),
            np.asarray(p3d.rgb, dtype=np.float32),
        )

    images: list[ImageRecord] = []
    for image_id, img in images_dict.items():
        pids = np.asarray(img.point3D_ids, dtype=np.int64)
        pids = pids[(pids != -1)]
        images.append(
            ImageRecord(
                image_id=int(image_id),
                name=str(img.name),
                point3d_ids=pids,
            )
        )
    return images, points, "read_write_model"


def load_colmap_data(sparse_dir: Path) -> tuple[list[ImageRecord], dict[int, tuple[np.ndarray, np.ndarray]], str]:
    try:
        return _load_with_pycolmap(sparse_dir)
    except Exception:  # noqa: BLE001
        return _load_with_rw_model(sparse_dir)


def extract_frame_idx(image_name: str) -> int | None:
    for pat in FRAME_PATTERNS:
        match = pat.search(image_name)
        if match:
            return int(match.group(1))
    return None


def group_images_by_frame(images: Iterable[ImageRecord]) -> dict[int, dict[str, object]]:
    sorted_images = sorted(images, key=lambda x: x.name)
    groups: dict[int, dict[str, object]] = {}
    fallback_idx = 0
    for img in sorted_images:
        frame_idx = extract_frame_idx(img.name)
        if frame_idx is None:
            frame_idx = fallback_idx
            fallback_idx += 1
        entry = groups.setdefault(
            frame_idx,
            {
                "image_ids": [],
                "image_names": [],
                "point_ids": set(),
            },
        )
        entry["image_ids"].append(int(img.image_id))
        entry["image_names"].append(str(img.name))
        entry["point_ids"].update(int(pid) for pid in img.point3d_ids)
    return groups


def sample_points(
    point_ids: np.ndarray,
    points_dict: dict[int, tuple[np.ndarray, np.ndarray]],
    max_points: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    if point_ids.size == 0:
        return np.zeros((0, 3), dtype=np.float32), np.zeros((0, 3), dtype=np.float32)

    unique_ids = np.unique(point_ids)
    unique_ids = np.asarray([pid for pid in unique_ids if int(pid) in points_dict], dtype=np.int64)
    if max_points > 0 and unique_ids.size > max_points:
        unique_ids = rng.choice(unique_ids, size=max_points, replace=False)

    xyz = np.asarray([points_dict[int(pid)][0] for pid in unique_ids], dtype=np.float32)
    rgb = np.asarray([points_dict[int(pid)][1] for pid in unique_ids], dtype=np.float32)
    return xyz, rgb


def selected_frames(
    frames: list[int],
    frame_start: int,
    frame_end: int,
    keyframe_step: int,
    keyframe_emit: str,
) -> list[int]:
    selected = [f for f in frames if frame_start <= f < frame_end]
    if not selected:
        return []
    if keyframe_emit == "all" or keyframe_step <= 1:
        return selected

    frame_set = set(selected)
    first_frame = selected[0]
    emitted: set[int] = set()
    for frame_idx in selected:
        is_kf = ((frame_idx - first_frame) % keyframe_step) == 0
        if not is_kf:
            continue
        emitted.add(frame_idx)
        if keyframe_emit == "keyframes_with_next":
            next_f = frame_idx + 1
            if next_f in frame_set:
                emitted.add(next_f)
    return sorted(emitted)


def _save_or_link(
    arr: np.ndarray,
    target_path: Path,
    ref_path: Path | None,
    link_mode: str,
) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if ref_path is None or link_mode == "copy":
        np.save(target_path, arr)
        return

    if target_path.exists() or target_path.is_symlink():
        target_path.unlink()
    rel_ref = Path(os.path.relpath(ref_path, start=target_path.parent))
    target_path.symlink_to(rel_ref)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--colmap_data_dir", required=True, help="包含 images/ 与 sparse/0/ 的目录")
    ap.add_argument("--out_dir", required=True, help="输出 triangulation_input_dir")
    ap.add_argument(
        "--mode",
        choices=["visible_per_frame", "static_copy"],
        default="visible_per_frame",
        help="visible_per_frame: 每帧聚合可见点; static_copy: 每帧复制全局 points3D",
    )
    ap.add_argument("--frame_start", type=int, default=0, help="起始帧（包含）")
    ap.add_argument("--frame_end", type=int, default=-1, help="-1 表示到最后一帧（不包含上界）")
    ap.add_argument("--max_points", type=int, default=200_000, help="每帧最多保留点数，<=0 表示不截断")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--keyframe_step", type=int, default=1, help="仅导出关键帧时的步长")
    ap.add_argument(
        "--keyframe_emit",
        choices=["all", "keyframes", "keyframes_with_next"],
        default="all",
        help="all: 全帧; keyframes: 仅关键帧; keyframes_with_next: 关键帧+下一帧",
    )
    ap.add_argument(
        "--link_mode",
        choices=["copy", "symlink"],
        default="copy",
        help="static_copy 下重复内容可用 symlink 降低空间占用",
    )
    args = ap.parse_args()

    colmap_data_dir = Path(args.colmap_data_dir)
    sparse_dir = colmap_data_dir / "sparse" / "0"
    if not sparse_dir.exists():
        raise FileNotFoundError(f"COLMAP sparse not found: {sparse_dir}")

    images, points_dict, loader = load_colmap_data(sparse_dir)
    frame_groups = group_images_by_frame(images)
    all_frames = sorted(frame_groups.keys())

    if not all_frames:
        raise ValueError(f"No valid frame groups from COLMAP images: {sparse_dir}")

    frame_start = max(args.frame_start, all_frames[0])
    frame_end = (all_frames[-1] + 1) if args.frame_end < 0 else args.frame_end
    if frame_start >= frame_end:
        raise ValueError(
            f"Invalid frame range: start={frame_start}, end={frame_end}, available=[{all_frames[0]}, {all_frames[-1]}]"
        )

    emit_frames = selected_frames(
        frames=all_frames,
        frame_start=frame_start,
        frame_end=frame_end,
        keyframe_step=max(1, args.keyframe_step),
        keyframe_emit=args.keyframe_emit,
    )
    if not emit_frames:
        raise ValueError(
            f"No frames selected with range [{frame_start}, {frame_end}) and keyframe_emit={args.keyframe_emit}"
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    manifest_path = out_dir / "frame_manifest.csv"

    static_ids = np.asarray(sorted(points_dict.keys()), dtype=np.int64)
    static_xyz = static_rgb = None
    if args.mode == "static_copy":
        static_xyz, static_rgb = sample_points(static_ids, points_dict, args.max_points, rng)

    print(f"[Info] COLMAP dir: {colmap_data_dir}")
    print(f"[Info] Sparse dir: {sparse_dir}")
    print(f"[Info] Loader: {loader}")
    print(f"[Info] Mode: {args.mode}")
    print(f"[Info] Selected frames: {len(emit_frames)} / {len(all_frames)}")
    print(f"[Info] Frame range: [{frame_start}, {frame_end})")
    print(f"[Info] Keyframe emit: {args.keyframe_emit}, step={args.keyframe_step}")
    print(f"[Info] Link mode: {args.link_mode}")
    print(f"[Info] Max points/frame: {args.max_points}")
    print(f"[Info] Output dir: {out_dir}")

    ref_points_path: Path | None = None
    ref_colors_path: Path | None = None

    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "frame_idx",
                "num_images",
                "num_points",
                "mode",
                "is_keyframe",
                "image_ids",
                "image_names",
            ]
        )

        for frame_idx in emit_frames:
            group = frame_groups.get(frame_idx)
            if group is None:
                continue

            if args.mode == "static_copy":
                assert static_xyz is not None and static_rgb is not None
                xyz, rgb = static_xyz, static_rgb
            else:
                pids = np.asarray(sorted(group["point_ids"]), dtype=np.int64)
                xyz, rgb = sample_points(pids, points_dict, args.max_points, rng)

            points_path = out_dir / f"points3d_frame{frame_idx:06d}.npy"
            colors_path = out_dir / f"colors_frame{frame_idx:06d}.npy"

            can_link = args.mode == "static_copy" and args.link_mode == "symlink" and ref_points_path is not None
            _save_or_link(
                arr=xyz,
                target_path=points_path,
                ref_path=ref_points_path if can_link else None,
                link_mode=args.link_mode,
            )
            _save_or_link(
                arr=rgb,
                target_path=colors_path,
                ref_path=ref_colors_path if can_link else None,
                link_mode=args.link_mode,
            )

            if ref_points_path is None:
                ref_points_path = points_path
                ref_colors_path = colors_path

            is_keyframe = 1 if ((frame_idx - emit_frames[0]) % max(args.keyframe_step, 1) == 0) else 0
            writer.writerow(
                [
                    frame_idx,
                    len(group["image_ids"]),
                    int(xyz.shape[0]),
                    args.mode,
                    is_keyframe,
                    ";".join(map(str, group["image_ids"])),
                    ";".join(map(str, group["image_names"])),
                ]
            )
            print(f"[{frame_idx:06d}] images={len(group['image_ids'])} points={xyz.shape[0]}")

    print(f"\nDone. Wrote: {out_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
