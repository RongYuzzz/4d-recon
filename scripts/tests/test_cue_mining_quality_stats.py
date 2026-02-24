#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
CUE_SCRIPT = REPO_ROOT / "scripts" / "cue_mining.py"


def _make_tiny_dataset(root: Path, cams: list[str], frames: int) -> Path:
    data_dir = root / "toy_data"
    images_dir = data_dir / "images"
    h, w = 24, 32
    for cam_i, cam in enumerate(cams):
        cam_dir = images_dir / cam
        cam_dir.mkdir(parents=True, exist_ok=True)
        for t in range(frames):
            img = np.zeros((h, w, 3), dtype=np.uint8)
            img[..., 2] = 20 + cam_i * 60
            x0 = 1 + t * 4 + cam_i
            y0 = 5 + cam_i
            img[y0:y0 + 6, x0:x0 + 6] = np.array([250, 60, 80], dtype=np.uint8)
            Image.fromarray(img).save(cam_dir / f"{t:06d}.jpg", quality=95)
    return data_dir


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="cue_mining_quality_") as tmp:
        root = Path(tmp)
        cams = ["02", "03", "04"]
        frames = 4
        data_dir = _make_tiny_dataset(root, cams=cams, frames=frames)
        out_dir = root / "cue_out"

        cmd = [
            sys.executable,
            str(CUE_SCRIPT),
            "--data_dir",
            str(data_dir),
            "--out_dir",
            str(out_dir),
            "--frame_start",
            "0",
            "--num_frames",
            str(frames),
            "--mask_downscale",
            "4",
            "--backend",
            "diff",
            "--overwrite",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(
                "cue_mining.py failed\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )

        quality_path = out_dir / "quality.json"
        if not quality_path.exists():
            raise AssertionError(f"missing quality stats file: {quality_path}")

        quality = json.loads(quality_path.read_text(encoding="utf-8"))
        required_keys = {
            "mask_mean_per_t",
            "mask_mean_per_view",
            "mask_min",
            "mask_max",
            "temporal_flicker_l1_mean",
            "all_black",
            "all_white",
        }
        missing = sorted(required_keys - set(quality.keys()))
        if missing:
            raise AssertionError(f"quality.json missing keys: {missing}")

        if len(quality["mask_mean_per_t"]) != frames:
            raise AssertionError("mask_mean_per_t length mismatch")
        if len(quality["mask_mean_per_view"]) != len(cams):
            raise AssertionError("mask_mean_per_view length mismatch")

        if not isinstance(quality["all_black"], bool):
            raise AssertionError("all_black must be bool")
        if not isinstance(quality["all_white"], bool):
            raise AssertionError("all_white must be bool")

        for key in ("mask_min", "mask_max", "temporal_flicker_l1_mean"):
            if not isinstance(quality[key], (int, float)):
                raise AssertionError(f"{key} must be numeric")

        for value in quality["mask_mean_per_t"]:
            if not (0.0 <= float(value) <= 1.0):
                raise AssertionError(f"mask_mean_per_t out of range: {value}")
        for value in quality["mask_mean_per_view"]:
            if not (0.0 <= float(value) <= 1.0):
                raise AssertionError(f"mask_mean_per_view out of range: {value}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: cue_mining quality stats contract is valid")
