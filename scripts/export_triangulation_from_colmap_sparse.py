#!/usr/bin/env python3
"""
从 COLMAP sparse 导出 FreeTimeGS 所需的逐帧 A 类输入数据：
- points3d_frameXXXXXX.npy
- colors_frameXXXXXX.npy

目的：在缺少 ROMA/上游三角化链路时，先跑通 T0 审计闭环。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pycolmap


def load_reconstruction(sparse_dir: Path):
    """兼容不同 pycolmap API 的 Reconstruction 初始化方式。"""
    try:
        rec = pycolmap.Reconstruction()
        rec.read(str(sparse_dir))
        return rec
    except TypeError:
        return pycolmap.Reconstruction(str(sparse_dir))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--colmap_data_dir", required=True, help="包含 images/ 与 sparse/0/ 的目录")
    ap.add_argument("--out_dir", required=True, help="输出 triangulation_input_dir")
    ap.add_argument("--frame_start", type=int, default=0, help="起始帧（包含）")
    ap.add_argument("--frame_end", type=int, default=-1, help="-1 表示到最后一帧（不包含上界）")
    ap.add_argument("--max_points", type=int, default=200_000, help="每帧最多保留点数，<=0 表示不截断")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    colmap_data_dir = Path(args.colmap_data_dir)
    sparse_dir = colmap_data_dir / "sparse" / "0"
    if not sparse_dir.exists():
        raise FileNotFoundError(f"COLMAP sparse not found: {sparse_dir}")

    rec = load_reconstruction(sparse_dir)
    if not rec.images:
        raise ValueError(f"No images in reconstruction: {sparse_dir}")
    if not rec.points3D:
        raise ValueError(f"No points3D in reconstruction: {sparse_dir}")

    # 按 image.name 排序近似时间顺序
    image_ids = sorted(rec.images.keys(), key=lambda i: rec.images[i].name)

    frame_start = max(0, args.frame_start)
    frame_end = len(image_ids) if args.frame_end < 0 else min(args.frame_end, len(image_ids))
    if frame_start >= frame_end:
        raise ValueError(
            f"Invalid frame range: start={frame_start}, end={frame_end}, total={len(image_ids)}"
        )

    image_ids = image_ids[frame_start:frame_end]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    manifest_path = out_dir / "frame_manifest.csv"

    print(f"[Info] COLMAP dir: {colmap_data_dir}")
    print(f"[Info] Sparse dir: {sparse_dir}")
    print(f"[Info] Selected frames: [{frame_start}, {frame_end}) -> {len(image_ids)}")
    print(f"[Info] Max points/frame: {args.max_points}")
    print(f"[Info] Output dir: {out_dir}")

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("frame_idx,image_id,image_name,num_points\n")

        for frame_idx, image_id in enumerate(image_ids):
            img = rec.images[image_id]

            # 收集该图像内可见的 3D 点 ID
            p3d_ids = []
            for p2d in img.points2D:
                pid = int(getattr(p2d, "point3D_id", -1))
                if pid != -1 and pid in rec.points3D:
                    p3d_ids.append(pid)

            if not p3d_ids:
                xyz = np.zeros((0, 3), dtype=np.float32)
                rgb = np.zeros((0, 3), dtype=np.float32)
            else:
                p3d_ids = np.unique(np.asarray(p3d_ids, dtype=np.int64))
                if args.max_points > 0 and len(p3d_ids) > args.max_points:
                    p3d_ids = rng.choice(p3d_ids, size=args.max_points, replace=False)

                xyz_list = []
                rgb_list = []
                for pid in p3d_ids:
                    p3d = rec.points3D[int(pid)]
                    xyz_list.append(p3d.xyz)
                    rgb_list.append(p3d.color)  # uint8 0-255

                xyz = np.asarray(xyz_list, dtype=np.float32)
                rgb = np.asarray(rgb_list, dtype=np.float32)

            np.save(out_dir / f"points3d_frame{frame_idx:06d}.npy", xyz)
            np.save(out_dir / f"colors_frame{frame_idx:06d}.npy", rgb)

            f.write(f"{frame_idx},{int(image_id)},{img.name},{xyz.shape[0]}\n")
            print(f"[{frame_idx:06d}] {img.name} -> {xyz.shape[0]} points")

    print(f"\nDone. Wrote: {out_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

