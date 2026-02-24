#!/usr/bin/env python3
"""TDD tests for scripts/prepare_selfcap_for_freetime.py."""

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

from read_write_model import read_model  # noqa: E402


def _write_mock_intri(intri_path: Path) -> None:
    intri_path.write_text(
        """%YAML:1.0
---
K_02: !!opencv-matrix
  rows: 3
  cols: 3
  dt: d
  data: [500.0, 0.0, 320.0, 0.0, 510.0, 240.0, 0.0, 0.0, 1.0]
dist_02: !!opencv-matrix
  rows: 1
  cols: 5
  dt: d
  data: [0.0, 0.0, 0.0, 0.0, 0.0]
K_03: !!opencv-matrix
  rows: 3
  cols: 3
  dt: d
  data: [520.0, 0.0, 300.0, 0.0, 525.0, 250.0, 0.0, 0.0, 1.0]
dist_03: !!opencv-matrix
  rows: 1
  cols: 5
  dt: d
  data: [0.0, 0.0, 0.0, 0.0, 0.0]
names:
  - "02"
  - "03"
""",
        encoding="utf-8",
    )


def _write_mock_extri(extri_path: Path) -> None:
    extri_path.write_text(
        """%YAML:1.0
---
Rot_02: !!opencv-matrix
  rows: 3
  cols: 3
  dt: d
  data: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
T_02: !!opencv-matrix
  rows: 3
  cols: 1
  dt: d
  data: [0.0, 0.0, 0.0]
Rot_03: !!opencv-matrix
  rows: 3
  cols: 3
  dt: d
  data: [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
T_03: !!opencv-matrix
  rows: 3
  cols: 1
  dt: d
  data: [1.0, 2.0, 3.0]
""",
        encoding="utf-8",
    )


def _write_binary_ply(path: Path, xyz: np.ndarray, rgb: np.ndarray) -> None:
    if xyz.shape != rgb.shape or xyz.shape[1] != 3:
        raise AssertionError("xyz/rgb shape mismatch")

    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {xyz.shape[0]}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "property uchar red\n"
        "property uchar green\n"
        "property uchar blue\n"
        "end_header\n"
    ).encode("ascii")

    data = np.empty(
        xyz.shape[0],
        dtype=[
            ("x", "<f4"),
            ("y", "<f4"),
            ("z", "<f4"),
            ("red", "u1"),
            ("green", "u1"),
            ("blue", "u1"),
        ],
    )
    data["x"] = xyz[:, 0]
    data["y"] = xyz[:, 1]
    data["z"] = xyz[:, 2]
    data["red"] = rgb[:, 0]
    data["green"] = rgb[:, 1]
    data["blue"] = rgb[:, 2]

    with path.open("wb") as f:
        f.write(header)
        data.tofile(f)


def _create_mock_selfcap(root: Path) -> None:
    (root / "optimized").mkdir(parents=True, exist_ok=True)
    (root / "pcds").mkdir(parents=True, exist_ok=True)
    (root / "videos").mkdir(parents=True, exist_ok=True)

    _write_mock_intri(root / "optimized" / "intri.yml")
    _write_mock_extri(root / "optimized" / "extri.yml")

    xyz0 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0]], dtype=np.float32)
    rgb0 = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8)
    xyz1 = np.array([[0, 0, 1], [1, 0, 1], [1, 1, 1]], dtype=np.float32)
    rgb1 = np.array([[255, 255, 0], [0, 255, 255], [255, 0, 255]], dtype=np.uint8)
    _write_binary_ply(root / "pcds" / "000000.ply", xyz0, rgb0)
    _write_binary_ply(root / "pcds" / "000001.ply", xyz1, rgb1)


def test_selfcap_adapter_should_generate_colmap_and_triangulation() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        selfcap_root = tmp / "bar-release"
        out_root = tmp / "scene01"
        _create_mock_selfcap(selfcap_root)

        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "prepare_selfcap_for_freetime.py"),
            "--selfcap_root",
            str(selfcap_root),
            "--out_root",
            str(out_root),
            "--frame_start",
            "0",
            "--frame_end",
            "2",
            "--image_width",
            "640",
            "--image_height",
            "480",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                "adapter script failed\n"
                f"cmd: {' '.join(cmd)}\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}\n"
            )

        tri = out_root / "triangulation"
        p0 = np.load(tri / "points3d_frame000000.npy")
        c0 = np.load(tri / "colors_frame000000.npy")
        p1 = np.load(tri / "points3d_frame000001.npy")
        c1 = np.load(tri / "colors_frame000001.npy")
        if p0.shape != (3, 3) or c0.shape != (3, 3):
            raise AssertionError("Unexpected shape for frame000000")
        if p1.shape != (3, 3) or c1.shape != (3, 3):
            raise AssertionError("Unexpected shape for frame000001")

        sparse_dir = out_root / "colmap" / "sparse" / "0"
        cams, imgs, pts = read_model(str(sparse_dir), ext=".bin")
        if len(cams) != 2:
            raise AssertionError(f"Expected 2 cameras, got {len(cams)}")
        if len(imgs) != 2:
            raise AssertionError(f"Expected 2 images, got {len(imgs)}")
        if len(pts) == 0:
            raise AssertionError("Expected non-empty points3D")

        image_names = sorted(img.name for img in imgs.values())
        if image_names != ["02.jpg", "03.jpg"]:
            raise AssertionError(f"Unexpected image names: {image_names}")

        manifest = out_root / "triangulation" / "frame_manifest.csv"
        rows = list(csv.DictReader(manifest.open("r", encoding="utf-8")))
        if len(rows) != 2:
            raise AssertionError(f"Expected 2 manifest rows, got {len(rows)}")


if __name__ == "__main__":
    try:
        test_selfcap_adapter_should_generate_colmap_and_triangulation()
    except Exception as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: selfcap adapter tests")
