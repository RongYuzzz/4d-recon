#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_vggt_preprocess_consistency.py"


def _make_tiny_dataset(root: Path, cams: list[str], frames: int) -> Path:
    data_dir = root / "toy_data"
    images_dir = data_dir / "images"
    h, w = 48, 64
    for cam_i, cam in enumerate(cams):
        cam_dir = images_dir / cam
        cam_dir.mkdir(parents=True, exist_ok=True)
        for t in range(frames):
            img = np.zeros((h, w, 3), dtype=np.uint8)
            img[..., 0] = 30 + cam_i * 60
            img[..., 1] = 20 + t * 30
            img[..., 2] = 110
            img[10 + cam_i : 22 + cam_i, 8 + t * 2 : 20 + t * 2, :] = np.array(
                [220, 210, 30], dtype=np.uint8
            )
            Image.fromarray(img).save(cam_dir / f"{t:06d}.jpg", quality=95)
    return data_dir


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="vggt_preprocess_consistency_dummy_") as td:
        root = Path(td)
        cams = ["02", "03"]
        frames = 3
        data_dir = _make_tiny_dataset(root, cams=cams, frames=frames)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--backend",
            "dummy",
            "--data_dir",
            str(data_dir),
            "--camera_ids",
            ",".join(cams),
            "--frame_start",
            "0",
            "--num_frames",
            str(frames),
            "--phi_downscale",
            "4",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            raise AssertionError(
                "check_vggt_preprocess_consistency.py failed\n"
                f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
            )
        merged = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if "PASS" not in merged:
            raise AssertionError(f"expected PASS in output, got:\n{merged}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: vggt preprocess consistency dummy mode")
