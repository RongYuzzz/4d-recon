#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "adapt_thuman4_release_to_freetime.py"


def _write_rgb(path: Path, color: tuple[int, int, int]) -> None:
    arr = np.zeros((16, 20, 3), dtype=np.uint8)
    arr[..., 0] = color[0]
    arr[..., 1] = color[1]
    arr[..., 2] = color[2]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path, quality=95)


def _write_mask(path: Path, on: bool) -> None:
    arr = np.zeros((16, 20), dtype=np.uint8)
    if on:
        arr[3:13, 4:16] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def test_adapter_builds_expected_layout() -> None:
    with tempfile.TemporaryDirectory(prefix="thuman4_adapter_") as td:
        root = Path(td)
        src = root / "thuman_subject00"
        for cam in ["c0", "c1"]:
            for t in range(3):
                _write_rgb(src / "images" / cam / f"{t:06d}.jpg", (30 + t, 50, 70))
                _write_mask(src / "masks" / cam / f"{t:06d}.png", on=(t != 0))

        out_dir = root / "out_data"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--input_dir",
            str(src),
            "--output_dir",
            str(out_dir),
            "--camera_ids",
            "c0,c1",
            "--output_camera_ids",
            "02,03",
            "--frame_start",
            "0",
            "--num_frames",
            "3",
            "--image_downscale",
            "2",
            "--copy_mode",
            "copy",
            "--overwrite",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )

        assert (out_dir / "images" / "02" / "000000.jpg").exists()
        assert (out_dir / "images" / "03" / "000002.jpg").exists()
        assert (out_dir / "masks" / "02" / "000001.png").exists()
        assert (out_dir / "masks" / "03" / "000002.png").exists()
        assert (out_dir / "adapt_manifest.csv").exists()
        assert (out_dir / "adapt_scene.json").exists()
