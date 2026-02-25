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
SCRIPT = REPO_ROOT / "scripts" / "precompute_vggt_cache.py"


def _make_tiny_dataset(root: Path, cams: list[str], frames: int) -> Path:
    data_dir = root / "toy_data"
    images_dir = data_dir / "images"
    h, w = 48, 64
    for cam_i, cam in enumerate(cams):
        cam_dir = images_dir / cam
        cam_dir.mkdir(parents=True, exist_ok=True)
        for t in range(frames):
            img = np.zeros((h, w, 3), dtype=np.uint8)
            img[..., 0] = 20 + cam_i * 50
            img[..., 1] = 40 + t * 20
            img[..., 2] = 120
            img[8 + cam_i : 20 + cam_i, 10 + t * 3 : 22 + t * 3, :] = np.array(
                [220, 200, 20], dtype=np.uint8
            )
            Image.fromarray(img).save(cam_dir / f"{t:06d}.jpg", quality=95)
    return data_dir


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="vggt_cache_contract_") as tmp:
        root = Path(tmp)
        cams = ["02", "03"]
        frames = 3
        data_dir = _make_tiny_dataset(root, cams=cams, frames=frames)
        out_dir = root / "cache_out"

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--out_dir",
            str(out_dir),
            "--camera_ids",
            ",".join(cams),
            "--frame_start",
            "0",
            "--num_frames",
            str(frames),
            "--backend",
            "dummy",
            "--phi_name",
            "dummy_rgb",
            "--phi_downscale",
            "4",
            "--overwrite",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(
                "precompute_vggt_cache.py failed\n"
                f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
            )

        npz_path = out_dir / "gt_cache.npz"
        meta_path = out_dir / "meta.json"
        if not npz_path.exists():
            raise AssertionError(f"missing output npz: {npz_path}")
        if not meta_path.exists():
            raise AssertionError(f"missing output meta: {meta_path}")

        obj = np.load(npz_path, allow_pickle=True)
        required_keys = {
            "phi",
            "camera_names",
            "frame_start",
            "num_frames",
            "phi_name",
            "vggt_mode",
            "input_size",
            "phi_size",
        }
        # Keep contract backward-compatible: only assert required baseline keys.
        # New cache variants may add optional keys (e.g., conf/gate_framediff/token_*).
        missing = sorted(required_keys - set(obj.files))
        if missing:
            raise AssertionError(f"missing keys in npz: {', '.join(missing)}")

        phi = obj["phi"]
        if phi.ndim != 5:
            raise AssertionError(f"phi.ndim must be 5, got {phi.ndim}")
        if phi.shape[0] != frames:
            raise AssertionError(f"T mismatch: expected {frames}, got {phi.shape[0]}")
        if phi.shape[1] != len(cams):
            raise AssertionError(f"V mismatch: expected {len(cams)}, got {phi.shape[1]}")
        if phi.shape[2] <= 0:
            raise AssertionError(f"C must be >0, got {phi.shape[2]}")
        if phi.dtype not in (np.float16, np.float32):
            raise AssertionError(f"phi dtype must be float16/float32, got {phi.dtype}")

        camera_names = [str(x) for x in obj["camera_names"].tolist()]
        if camera_names != cams:
            raise AssertionError(f"camera_names mismatch: expected {cams}, got {camera_names}")

        if int(obj["frame_start"]) != 0:
            raise AssertionError(f"frame_start mismatch: {int(obj['frame_start'])}")
        if int(obj["num_frames"]) != frames:
            raise AssertionError(f"num_frames mismatch: {int(obj['num_frames'])}")
        if str(obj["phi_name"].item()) != "dummy_rgb":
            raise AssertionError(f"phi_name mismatch: {obj['phi_name'].item()}")
        if str(obj["vggt_mode"].item()) != "crop":
            raise AssertionError(f"vggt_mode mismatch: {obj['vggt_mode'].item()}")

        input_size = np.asarray(obj["input_size"]).astype(int).tolist()
        phi_size = np.asarray(obj["phi_size"]).astype(int).tolist()
        if len(input_size) != 2 or len(phi_size) != 2:
            raise AssertionError(
                f"input_size/phi_size must be length=2, got {input_size}, {phi_size}"
            )
        if phi.shape[3:] != tuple(phi_size):
            raise AssertionError(
                f"phi shape HW mismatch with phi_size: {phi.shape[3:]} vs {tuple(phi_size)}"
            )

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta_required = {
            "camera_names",
            "frame_start",
            "num_frames",
            "phi_name",
            "vggt_mode",
            "input_size",
            "phi_size",
        }
        for key in meta_required:
            if key not in meta:
                raise AssertionError(f"missing key in meta.json: {key}")
        if meta["camera_names"] != cams:
            raise AssertionError(f"meta camera_names mismatch: {meta['camera_names']}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: VGGT cache contract outputs are valid")
