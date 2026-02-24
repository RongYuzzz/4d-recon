#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SCRIPT = REPO_ROOT / "scripts" / "adapt_hf_sample_to_freetime.py"
RW_PATH = (
    REPO_ROOT
    / "third_party"
    / "FreeTimeGsVanilla"
    / "datasets"
    / "read_write_model.py"
)


def load_rw_module():
    spec = importlib.util.spec_from_file_location("rw", RW_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module at {RW_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_toy_colmap(sparse_dir: Path, rw) -> None:
    Camera = rw.Camera
    Image = rw.Image
    Point3D = rw.Point3D

    cameras = {
        1: Camera(
            id=1,
            model="PINHOLE",
            width=64,
            height=48,
            params=np.array([40.0, 40.0, 32.0, 24.0], dtype=np.float64),
        )
    }
    images = {
        1: Image(
            id=1,
            qvec=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            tvec=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            camera_id=1,
            name="camA.jpg",
            xys=np.array([[10.0, 10.0]], dtype=np.float64),
            point3D_ids=np.array([1], dtype=np.int64),
        )
    }
    points3d = {
        1: Point3D(
            id=1,
            xyz=np.array([0.0, 0.0, 1.0], dtype=np.float64),
            rgb=np.array([200, 120, 50], dtype=np.uint8),
            error=0.1,
            image_ids=np.array([1], dtype=np.int32),
            point2D_idxs=np.array([0], dtype=np.int32),
        )
    }
    sparse_dir.mkdir(parents=True, exist_ok=True)
    rw.write_model(cameras, images, points3d, str(sparse_dir), ext=".bin")


def write_frame_points(frame_dir: Path, rw, x_value: float) -> None:
    Point3D = rw.Point3D
    points = {
        1: Point3D(
            id=1,
            xyz=np.array([x_value, 0.0, 1.0], dtype=np.float64),
            rgb=np.array([10, 20, 30], dtype=np.uint8),
            error=0.1,
            image_ids=np.array([1], dtype=np.int32),
            point2D_idxs=np.array([0], dtype=np.int32),
        )
    }
    frame_dir.mkdir(parents=True, exist_ok=True)
    rw.write_points3D_binary(points, str(frame_dir / "points3D.bin"))


def run_test() -> None:
    rw = load_rw_module()
    with tempfile.TemporaryDirectory(prefix="adapt_hf_per_frame_test_") as tmp:
        root = Path(tmp)
        source_dir = root / "source"
        (source_dir / "images").mkdir(parents=True, exist_ok=True)
        (source_dir / "images" / "camA.jpg").write_bytes(b"fake-jpeg")

        sparse0 = source_dir / "sparse" / "0"
        build_toy_colmap(sparse0, rw)

        # Non-zero-padded names on purpose: numeric sorting must still be correct.
        write_frame_points(source_dir / "sparse" / "frame_10", rw, x_value=10.0)
        write_frame_points(source_dir / "sparse" / "frame_2", rw, x_value=2.0)

        output_dir = root / "out"
        cmd = [
            sys.executable,
            str(ADAPTER_SCRIPT),
            "--source_dir",
            str(source_dir),
            "--output_dir",
            str(output_dir),
            "--num_frames",
            "4",
            "--copy_mode",
            "copy",
            "--triangulation_mode",
            "per_frame_sparse",
            "--per_frame_sparse_dir",
            str(source_dir / "sparse"),
            "--triangulation_frame_start",
            "0",
            "--triangulation_frame_end",
            "-1",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(
                "adapter script failed unexpectedly\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )

        tri_dir = output_dir / "triangulation"
        tri_points = sorted(p.name for p in tri_dir.glob("points3d_frame*.npy"))
        assert tri_points == ["points3d_frame000000.npy", "points3d_frame000001.npy"], tri_points

        xyz0 = np.load(tri_dir / "points3d_frame000000.npy")
        xyz1 = np.load(tri_dir / "points3d_frame000001.npy")
        assert xyz0.shape == (1, 3), xyz0.shape
        assert xyz1.shape == (1, 3), xyz1.shape
        assert float(xyz0[0, 0]) == 2.0, xyz0
        assert float(xyz1[0, 0]) == 10.0, xyz1

        with (tri_dir / "frame_manifest.csv").open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2, rows
        assert rows[0]["source_frame"] == "2", rows
        assert rows[1]["source_frame"] == "10", rows

    # All selected per-frame sparse dirs missing points3D -> should fail fast.
    with tempfile.TemporaryDirectory(prefix="adapt_hf_per_frame_empty_test_") as tmp:
        root = Path(tmp)
        source_dir = root / "source"
        (source_dir / "images").mkdir(parents=True, exist_ok=True)
        (source_dir / "images" / "camA.jpg").write_bytes(b"fake-jpeg")
        sparse0 = source_dir / "sparse" / "0"
        build_toy_colmap(sparse0, rw)
        (source_dir / "sparse" / "frame_000000").mkdir(parents=True, exist_ok=True)
        (source_dir / "sparse" / "frame_000001").mkdir(parents=True, exist_ok=True)

        output_dir = root / "out"
        cmd = [
            sys.executable,
            str(ADAPTER_SCRIPT),
            "--source_dir",
            str(source_dir),
            "--output_dir",
            str(output_dir),
            "--num_frames",
            "2",
            "--copy_mode",
            "copy",
            "--triangulation_mode",
            "per_frame_sparse",
            "--per_frame_sparse_dir",
            str(source_dir / "sparse"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            raise AssertionError("expected per_frame_sparse to fail when all selected frames miss points3D")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: adapt_hf_sample_to_freetime exports per_frame_sparse triangulation")
