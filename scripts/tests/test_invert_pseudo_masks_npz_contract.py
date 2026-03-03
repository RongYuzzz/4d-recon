#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "invert_pseudo_masks_npz.py"


def test_invert_npz_preserves_contract_and_inverts_values() -> None:
    with tempfile.TemporaryDirectory(prefix="invert_npz_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_npz = root / "out.npz"

        masks = np.zeros((2, 3, 4, 5), dtype=np.uint8)
        masks[0, 0, 1, 2] = 255
        masks[1, 2, 3, 4] = 7
        np.savez_compressed(
            in_npz,
            masks=masks,
            camera_names=np.asarray(["02", "03", "09"]),
            frame_start=np.int32(0),
            num_frames=np.int32(2),
            mask_downscale=np.int32(4),
        )

        r = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--in_npz",
                str(in_npz),
                "--out_npz",
                str(out_npz),
                "--overwrite",
            ],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"stdout:\n{r.stdout}\n\nstderr:\n{r.stderr}"
        assert out_npz.exists()

        obj = np.load(out_npz, allow_pickle=True)
        for key in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale"):
            assert key in obj.files
        out = obj["masks"]
        assert out.dtype == np.uint8
        assert out.shape == masks.shape
        assert int(out[0, 0, 1, 2]) == 0  # 255 -> 0
        assert int(out[1, 2, 3, 4]) == 248  # 7 -> 248

