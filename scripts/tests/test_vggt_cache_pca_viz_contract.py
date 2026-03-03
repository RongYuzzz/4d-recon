#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "viz_vggt_cache_pca.py"


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="vggt_cache_pca_viz_") as td:
        root = Path(td)
        cache_npz = root / "gt_cache.npz"
        out_dir = root / "viz_out"

        # Tiny cache that still supports PCA.
        phi = np.random.RandomState(0).randn(2, 2, 8, 3, 3).astype(np.float32)
        np.savez_compressed(
            cache_npz,
            phi=phi,
            camera_names=np.array(["02", "03"]),
            frame_start=np.int32(0),
            num_frames=np.int32(2),
            phi_name=np.array("token_proj"),
            vggt_mode=np.array("crop"),
            input_size=np.array([48, 64], dtype=np.int32),
            phi_size=np.array([3, 3], dtype=np.int32),
        )

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--cache_npz",
            str(cache_npz),
            "--out_dir",
            str(out_dir),
            "--frames",
            "0",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise AssertionError(
                "viz_vggt_cache_pca.py failed\n"
                f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
            )

        required = [
            out_dir / "pca_rgb_cam02_frame000000.jpg",
            out_dir / "grid_pca_frame000000.jpg",
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise AssertionError("missing PCA viz outputs: " + ", ".join(missing))


def test_vggt_cache_pca_viz_contract() -> None:
    run_test()


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: VGGT cache PCA viz script writes required outputs")
