#!/usr/bin/env python3
from __future__ import annotations

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
        ),
        2: Camera(
            id=2,
            model="PINHOLE",
            width=64,
            height=48,
            params=np.array([40.0, 40.0, 32.0, 24.0], dtype=np.float64),
        ),
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
        ),
        2: Image(
            id=2,
            qvec=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            tvec=np.array([0.2, 0.0, 0.0], dtype=np.float64),
            camera_id=2,
            name="camB.jpg",
            xys=np.array([[12.0, 12.0]], dtype=np.float64),
            point3D_ids=np.array([1], dtype=np.int64),
        ),
    }

    points3d = {
        1: Point3D(
            id=1,
            xyz=np.array([0.0, 0.0, 1.0], dtype=np.float64),
            rgb=np.array([200, 120, 50], dtype=np.uint8),
            error=0.1,
            image_ids=np.array([1, 2], dtype=np.int32),
            point2D_idxs=np.array([0, 0], dtype=np.int32),
        )
    }

    sparse_dir.mkdir(parents=True, exist_ok=True)
    rw.write_model(cameras, images, points3d, str(sparse_dir), ext=".bin")


def run_test() -> None:
    rw = load_rw_module()
    with tempfile.TemporaryDirectory(prefix="adapt_hf_sample_test_") as tmp:
        root = Path(tmp)
        source_dir = root / "source"
        source_images = source_dir / "images"
        source_sparse = source_dir / "sparse" / "0"
        output_dir = root / "out"

        source_images.mkdir(parents=True, exist_ok=True)
        build_toy_colmap(source_sparse, rw)

        # Only one source image exists; camB should be filtered out.
        (source_images / "camA.jpg").write_bytes(b"fake-jpeg")

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
            "static_repeat",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(
                "adapter script failed unexpectedly\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )

        out_sparse = output_dir / "sparse" / "0"
        out_cameras, out_images, out_points = rw.read_model(str(out_sparse), ext=".bin")
        assert len(out_cameras) == 1, f"expected 1 camera, got {len(out_cameras)}"
        assert len(out_images) == 1, f"expected 1 image entry, got {len(out_images)}"
        out_img = next(iter(out_images.values()))
        assert out_img.name == "camA.jpg", f"unexpected image name: {out_img.name}"

        assert len(out_points) == 1, f"expected 1 point, got {len(out_points)}"
        point = next(iter(out_points.values()))
        assert point.image_ids.tolist() == [1], f"unexpected point track ids: {point.image_ids.tolist()}"

        cam_folder = output_dir / "images" / "camA"
        frame_names = sorted(p.name for p in cam_folder.glob("*.jpg"))
        assert frame_names == ["000000.jpg", "000001.jpg", "000002.jpg", "000003.jpg"], frame_names
        assert not (output_dir / "images" / "camB").exists(), "camB folder should be filtered out"

        tri_dir = output_dir / "triangulation"
        tri_points = sorted(p.name for p in tri_dir.glob("points3d_frame*.npy"))
        tri_colors = sorted(p.name for p in tri_dir.glob("colors_frame*.npy"))
        assert tri_points == [
            "points3d_frame000000.npy",
            "points3d_frame000001.npy",
            "points3d_frame000002.npy",
            "points3d_frame000003.npy",
        ], tri_points
        assert tri_colors == [
            "colors_frame000000.npy",
            "colors_frame000001.npy",
            "colors_frame000002.npy",
            "colors_frame000003.npy",
        ], tri_colors

        xyz0 = np.load(tri_dir / "points3d_frame000000.npy")
        xyz3 = np.load(tri_dir / "points3d_frame000003.npy")
        rgb0 = np.load(tri_dir / "colors_frame000000.npy")
        assert xyz0.shape == (1, 3), xyz0.shape
        assert np.allclose(xyz0, xyz3), "static_repeat should output identical xyz across frames"
        assert rgb0.shape == (1, 3), rgb0.shape

        # Re-run with triangulation_mode=none; stale triangulation dir should be removed.
        cmd_none = [
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
            "none",
        ]
        result_none = subprocess.run(cmd_none, capture_output=True, text=True)
        if result_none.returncode != 0:
            raise AssertionError(
                "adapter script (triangulation_mode=none) failed unexpectedly\n"
                f"stdout:\n{result_none.stdout}\n\nstderr:\n{result_none.stderr}"
            )
        assert not tri_dir.exists(), "triangulation dir should be removed in triangulation_mode=none"


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: adapt_hf_sample_to_freetime filters sparse model and builds frame folders")
