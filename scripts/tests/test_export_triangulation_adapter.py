#!/usr/bin/env python3
"""TDD tests for scripts/export_triangulation_from_colmap_sparse.py."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = ROOT / "third_party" / "FreeTimeGsVanilla" / "datasets"
sys.path.insert(0, str(DATASETS_DIR))

from read_write_model import Camera, Image, Point3D, write_model  # noqa: E402


def _create_mock_colmap(colmap_dir: Path, n_frames: int, n_cams: int) -> None:
    sparse_dir = colmap_dir / "sparse" / "0"
    sparse_dir.mkdir(parents=True, exist_ok=True)
    (colmap_dir / "images").mkdir(parents=True, exist_ok=True)

    cameras = {
        1: Camera(
            id=1,
            model="PINHOLE",
            width=640,
            height=480,
            params=np.array([500.0, 500.0, 320.0, 240.0], dtype=np.float64),
        )
    }

    image_ids = []
    images = {}
    image_id = 1
    for frame_idx in range(n_frames):
        for cam_idx in range(n_cams):
            name = f"cam{cam_idx:02d}_frame{frame_idx:06d}.jpg"
            image_ids.append(image_id)
            images[image_id] = Image(
                id=image_id,
                qvec=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
                tvec=np.zeros(3, dtype=np.float64),
                camera_id=1,
                name=name,
                xys=np.array([[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]], dtype=np.float64),
                point3D_ids=np.array([1, 2, 3], dtype=np.int64),
            )
            image_id += 1

    points3d = {
        1: Point3D(
            id=1,
            xyz=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            rgb=np.array([255, 0, 0], dtype=np.uint8),
            error=0.0,
            image_ids=np.array(image_ids, dtype=np.int32),
            point2D_idxs=np.zeros(len(image_ids), dtype=np.int32),
        ),
        2: Point3D(
            id=2,
            xyz=np.array([1.0, 0.0, 0.0], dtype=np.float64),
            rgb=np.array([0, 255, 0], dtype=np.uint8),
            error=0.0,
            image_ids=np.array(image_ids, dtype=np.int32),
            point2D_idxs=np.zeros(len(image_ids), dtype=np.int32),
        ),
        3: Point3D(
            id=3,
            xyz=np.array([0.0, 1.0, 0.0], dtype=np.float64),
            rgb=np.array([0, 0, 255], dtype=np.uint8),
            error=0.0,
            image_ids=np.array(image_ids, dtype=np.int32),
            point2D_idxs=np.zeros(len(image_ids), dtype=np.int32),
        ),
    }

    write_model(cameras, images, points3d, str(sparse_dir), ext=".bin")


def _run_export(colmap_dir: Path, out_dir: Path, extra_args: list[str]) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "export_triangulation_from_colmap_sparse.py"),
        "--colmap_data_dir",
        str(colmap_dir),
        "--out_dir",
        str(out_dir),
        *extra_args,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "export script failed\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )


def _assert_files_equal(a: Path, b: Path) -> None:
    arr_a = np.load(a)
    arr_b = np.load(b)
    if not np.array_equal(arr_a, arr_b):
        raise AssertionError(f"Arrays differ: {a} vs {b}")


def test_visible_mode_should_group_multicam_by_frame() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        colmap_dir = tmp / "colmap"
        out_dir = tmp / "triangulation"
        _create_mock_colmap(colmap_dir, n_frames=3, n_cams=2)

        _run_export(
            colmap_dir=colmap_dir,
            out_dir=out_dir,
            extra_args=[
                "--mode",
                "visible_per_frame",
                "--frame_start",
                "0",
                "--frame_end",
                "-1",
                "--max_points",
                "0",
            ],
        )

        points_files = sorted(out_dir.glob("points3d_frame*.npy"))
        colors_files = sorted(out_dir.glob("colors_frame*.npy"))
        if len(points_files) != 3:
            raise AssertionError(f"Expected 3 frame files, got {len(points_files)}")
        if len(colors_files) != 3:
            raise AssertionError(f"Expected 3 color files, got {len(colors_files)}")

        for pf, cf in zip(points_files, colors_files):
            p = np.load(pf)
            c = np.load(cf)
            if p.shape != (3, 3):
                raise AssertionError(f"Unexpected points shape {p.shape} for {pf}")
            if c.shape != (3, 3):
                raise AssertionError(f"Unexpected colors shape {c.shape} for {cf}")

        manifest = out_dir / "frame_manifest.csv"
        rows = list(csv.DictReader(manifest.open("r", encoding="utf-8")))
        if len(rows) != 3:
            raise AssertionError(f"Expected 3 manifest rows, got {len(rows)}")


def test_static_mode_should_support_keyframe_symlink() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        colmap_dir = tmp / "colmap"
        out_dir = tmp / "triangulation"
        _create_mock_colmap(colmap_dir, n_frames=6, n_cams=2)

        _run_export(
            colmap_dir=colmap_dir,
            out_dir=out_dir,
            extra_args=[
                "--mode",
                "static_copy",
                "--frame_start",
                "0",
                "--frame_end",
                "-1",
                "--max_points",
                "0",
                "--keyframe_step",
                "2",
                "--keyframe_emit",
                "keyframes",
                "--link_mode",
                "symlink",
            ],
        )

        expected = ["points3d_frame000000.npy", "points3d_frame000002.npy", "points3d_frame000004.npy"]
        got = [p.name for p in sorted(out_dir.glob("points3d_frame*.npy"))]
        if got != expected:
            raise AssertionError(f"Unexpected frame files:\nexpected={expected}\ngot={got}")

        p0 = out_dir / "points3d_frame000000.npy"
        p2 = out_dir / "points3d_frame000002.npy"
        p4 = out_dir / "points3d_frame000004.npy"
        if not p2.is_symlink():
            raise AssertionError("Expected points3d_frame000002.npy to be symlink")
        if not p4.is_symlink():
            raise AssertionError("Expected points3d_frame000004.npy to be symlink")
        _assert_files_equal(p0, p2)
        _assert_files_equal(p0, p4)

        c0 = out_dir / "colors_frame000000.npy"
        c2 = out_dir / "colors_frame000002.npy"
        c4 = out_dir / "colors_frame000004.npy"
        if not c2.is_symlink():
            raise AssertionError("Expected colors_frame000002.npy to be symlink")
        if not c4.is_symlink():
            raise AssertionError("Expected colors_frame000004.npy to be symlink")
        _assert_files_equal(c0, c2)
        _assert_files_equal(c0, c4)


if __name__ == "__main__":
    try:
        test_visible_mode_should_group_multicam_by_frame()
        test_static_mode_should_support_keyframe_symlink()
    except Exception as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: export_triangulation adapter tests")
