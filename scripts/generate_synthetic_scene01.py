#!/usr/bin/env python3
"""
Generate a tiny synthetic FreeTime-compatible dataset:
- data/scene01/colmap/images/<cam_name>/<frame>.jpg
- data/scene01/colmap/sparse/0/{cameras,images,points3D}.bin

This is a fallback dataset for pipeline smoke tests when real COLMAP data is unavailable.
"""

from __future__ import annotations

import math
import sys
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image as PILImage


def build_colmap_model(
    scene_dir: Path,
    cam_names: list[str],
    width: int,
    height: int,
    points_world: np.ndarray,
    points_rgb: np.ndarray,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    rw_path = repo_root / "third_party" / "FreeTimeGsVanilla" / "datasets" / "read_write_model.py"
    spec = importlib.util.spec_from_file_location("read_write_model", rw_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {rw_path}")
    rw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rw)
    Camera = rw.Camera
    Image = rw.Image
    Point3D = rw.Point3D
    write_model = rw.write_model

    sparse_dir = scene_dir / "sparse" / "0"
    sparse_dir.mkdir(parents=True, exist_ok=True)

    fx = fy = 240.0
    cx = width / 2.0
    cy = height / 2.0

    cameras = {}
    images = {}
    points3D = {}

    n_cams = len(cam_names)
    for i, cam_name in enumerate(cam_names, start=1):
        cameras[i] = Camera(
            id=i,
            model="PINHOLE",
            width=width,
            height=height,
            params=np.array([fx, fy, cx, cy], dtype=np.float64),
        )

        theta = (2.0 * math.pi * (i - 1)) / max(n_cams, 1)
        cam_center = np.array([0.45 * math.cos(theta), 0.15, 0.45 * math.sin(theta)], dtype=np.float64)
        qvec = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)  # Identity rotation.
        tvec = -cam_center  # With identity R, t = -C.

        points_cam = points_world + tvec[None, :]
        z = np.clip(points_cam[:, 2], 0.4, None)
        x = fx * (points_cam[:, 0] / z) + cx
        y = fy * (points_cam[:, 1] / z) + cy
        xys = np.stack([x, y], axis=1).astype(np.float64)

        pids = np.arange(1, points_world.shape[0] + 1, dtype=np.int64)
        images[i] = Image(
            id=i,
            qvec=qvec,
            tvec=tvec,
            camera_id=i,
            name=f"{cam_name}.jpg",
            xys=xys,
            point3D_ids=pids,
        )

    for pid, (xyz, rgb) in enumerate(zip(points_world, points_rgb), start=1):
        points3D[pid] = Point3D(
            id=pid,
            xyz=xyz.astype(np.float64),
            rgb=rgb.astype(np.uint8),
            error=0.5,
            image_ids=np.arange(1, len(cam_names) + 1, dtype=np.int32),
            point2D_idxs=np.full((len(cam_names),), pid - 1, dtype=np.int32),
        )

    write_model(cameras, images, points3D, str(sparse_dir), ext=".bin")


def generate_images(scene_dir: Path, cam_names: list[str], n_frames: int, width: int, height: int) -> None:
    images_root = scene_dir / "images"
    for cam_idx, cam_name in enumerate(cam_names):
        cam_dir = images_root / cam_name
        cam_dir.mkdir(parents=True, exist_ok=True)
        for frame_idx in range(n_frames):
            x = np.linspace(0, 1, width, dtype=np.float32)
            y = np.linspace(0, 1, height, dtype=np.float32)
            xx, yy = np.meshgrid(x, y)

            phase = (frame_idx / max(n_frames - 1, 1)) * 2.0 * math.pi + cam_idx * 0.8
            moving = 0.5 + 0.5 * np.sin(8.0 * xx + 6.0 * yy + phase)
            r = np.clip(255.0 * (0.35 + 0.65 * moving), 0, 255)
            g = np.clip(255.0 * (0.20 + 0.80 * yy), 0, 255)
            b = np.clip(255.0 * (0.20 + 0.80 * xx), 0, 255)

            cx = int((0.15 + 0.7 * (frame_idx / max(n_frames - 1, 1))) * width)
            cy = int((0.3 + 0.2 * math.sin(phase)) * height)
            rr, cc = np.ogrid[:height, :width]
            mask = (rr - cy) ** 2 + (cc - cx) ** 2 <= (min(width, height) // 10) ** 2
            r[mask] = 255
            g[mask] = 245
            b[mask] = 60

            img = np.stack([r, g, b], axis=-1).astype(np.uint8)
            PILImage.fromarray(img).save(cam_dir / f"{frame_idx:06d}.jpg", quality=95)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scene_dir = repo_root / "data" / "scene01" / "colmap"
    scene_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    n_points = 900
    points_world = np.column_stack(
        [
            rng.uniform(-0.6, 0.6, size=n_points),
            rng.uniform(-0.4, 0.4, size=n_points),
            rng.uniform(0.7, 1.5, size=n_points),
        ]
    ).astype(np.float64)
    points_rgb = rng.integers(20, 255, size=(n_points, 3), dtype=np.uint8)

    cam_names = ["cam00", "cam01", "cam02", "cam03"]
    n_frames = 24
    width, height = 320, 240

    generate_images(scene_dir, cam_names, n_frames=n_frames, width=width, height=height)
    build_colmap_model(scene_dir, cam_names, width, height, points_world, points_rgb)

    print(f"Generated synthetic scene at: {scene_dir}")
    print(f"Cameras: {len(cam_names)}, frames/cam: {n_frames}, points3D: {n_points}")


if __name__ == "__main__":
    main()
