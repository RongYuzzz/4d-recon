#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "scale_pseudo_masks_npz.py"


def _write_npz(path: Path) -> None:
    masks = np.array([[[[0, 10], [20, 30]]]], dtype=np.uint8)  # [T=1,V=1,H=2,W=2]
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        masks=masks,
        camera_names=np.asarray(["09"], dtype=object),
        frame_start=np.int32(0),
        num_frames=np.int32(1),
        mask_downscale=np.int32(4),
    )


def test_scale_dynamic_matches_numpy_quantile() -> None:
    with tempfile.TemporaryDirectory(prefix="scale_pseudo_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_npz = root / "out.npz"
        _write_npz(in_npz)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--in_npz",
            str(in_npz),
            "--out_npz",
            str(out_npz),
            "--quantile",
            "0.50",
            "--mode",
            "dynamic_scaled",
            "--overwrite",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
        assert out_npz.exists()

        with np.load(in_npz, allow_pickle=True) as din:
            m = din["masks"].astype(np.float32) / 255.0
        q = float(np.quantile(m.reshape(-1), 0.50))
        expected = np.clip(m / (q + 1e-6), 0.0, 1.0).astype(np.float32)

        with np.load(out_npz, allow_pickle=True) as dout:
            out = np.asarray(dout["masks"], dtype=np.float32)
            assert out.shape == expected.shape
            assert float(out.min()) >= 0.0
            assert float(out.max()) <= 1.0
            assert np.allclose(out, expected, atol=1e-6)


def test_scale_static_is_one_minus_dynamic() -> None:
    with tempfile.TemporaryDirectory(prefix="scale_pseudo_") as td:
        root = Path(td)
        in_npz = root / "in.npz"
        out_dyn = root / "dyn.npz"
        out_sta = root / "sta.npz"
        _write_npz(in_npz)

        base = [
            sys.executable,
            str(SCRIPT),
            "--in_npz",
            str(in_npz),
            "--quantile",
            "0.50",
            "--overwrite",
        ]
        subprocess.check_call(base + ["--out_npz", str(out_dyn), "--mode", "dynamic_scaled"])
        subprocess.check_call(
            base + ["--out_npz", str(out_sta), "--mode", "static_from_dynamic_scaled"]
        )

        with np.load(out_dyn, allow_pickle=True) as dd, np.load(out_sta, allow_pickle=True) as ds:
            dyn = np.asarray(dd["masks"], dtype=np.float32)
            sta = np.asarray(ds["masks"], dtype=np.float32)
        assert np.allclose(sta, 1.0 - dyn, atol=1e-6)
