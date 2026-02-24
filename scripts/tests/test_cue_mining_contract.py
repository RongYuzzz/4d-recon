#!/usr/bin/env python3
from __future__ import annotations

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
            img[..., 1] = 60 + cam_i * 50
            x0 = 2 + t * 4 + cam_i
            y0 = 4 + cam_i
            img[y0:y0 + 6, x0:x0 + 6] = np.array([220, 220, 30], dtype=np.uint8)
            Image.fromarray(img).save(cam_dir / f"{t:06d}.jpg", quality=95)
    return data_dir


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="cue_mining_contract_") as tmp:
        root = Path(tmp)
        cams = ["02", "03"]
        frames = 3
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
            "3",
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

        npz_path = out_dir / "pseudo_masks.npz"
        if not npz_path.exists():
            raise AssertionError(f"missing output npz: {npz_path}")

        obj = np.load(npz_path, allow_pickle=True)
        for key in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale"):
            if key not in obj:
                raise AssertionError(f"missing key in npz: {key}")

        masks = obj["masks"]
        if masks.ndim != 4:
            raise AssertionError(f"masks.ndim must be 4, got {masks.ndim}")

        t, v = masks.shape[0], masks.shape[1]
        if t != frames:
            raise AssertionError(f"T mismatch: expected {frames}, got {t}")
        if v != len(cams):
            raise AssertionError(f"V mismatch: expected {len(cams)}, got {v}")
        if masks.dtype != np.uint8:
            raise AssertionError(f"masks dtype must be uint8, got {masks.dtype}")

        camera_names = [str(x) for x in obj["camera_names"].tolist()]
        if camera_names != sorted(cams):
            raise AssertionError(f"camera_names mismatch: {camera_names}")

        if int(obj["frame_start"]) != 0:
            raise AssertionError(f"frame_start mismatch: {int(obj['frame_start'])}")
        if int(obj["num_frames"]) != frames:
            raise AssertionError(f"num_frames mismatch: {int(obj['num_frames'])}")

        overlay = out_dir / "viz" / "overlay_cam02_frame000000.jpg"
        grid = out_dir / "viz" / "grid_frame000000.jpg"
        if not overlay.exists():
            raise AssertionError(f"missing overlay: {overlay}")
        if not grid.exists():
            raise AssertionError(f"missing grid: {grid}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: cue_mining contract npz+viz outputs are valid")
