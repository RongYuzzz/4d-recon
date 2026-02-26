#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_phi_shift_sensitivity.py"


def _write_dummy_phi(npz_path: Path) -> None:
    h, w = 6, 6
    y, x = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
    phi_ch0 = x / (w - 1)  # horizontal gradient
    phi_ch1 = y / (h - 1)  # vertical gradient
    phi = np.stack([phi_ch0, phi_ch1], axis=0)[None, None, :, :, :]  # [1,1,2,H,W]
    np.savez(npz_path, phi=phi.astype(np.float32))


def _row(rows: list[dict[str, str]], dx: int, dy: int) -> dict[str, str]:
    for r in rows:
        if int(r["dx"]) == dx and int(r["dy"]) == dy:
            return r
    raise KeyError(f"missing row dx={dx},dy={dy}")


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="phi_shift_test_", dir=REPO_ROOT) as td:
        root = Path(td)
        cache_npz = root / "gt_cache.npz"
        out_dir = root / "outputs" / "report_pack" / "diagnostics"
        _write_dummy_phi(cache_npz)

        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--cache_npz",
                str(cache_npz),
                "--out_dir",
                str(out_dir),
                "--max_shift",
                "2",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"analyze_phi_shift_sensitivity failed:\n{proc.stdout}\n{proc.stderr}")

        out_csv = out_dir / "phi_shift_sensitivity.csv"
        out_png = out_dir / "phi_shift_sensitivity.png"
        if not out_csv.exists():
            raise AssertionError(f"missing csv: {out_csv}")
        if not out_png.exists():
            raise AssertionError(f"missing png: {out_png}")

        rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8", newline="")))
        if len(rows) != 25:
            raise AssertionError(f"expected 25 rows for max_shift=2, got {len(rows)}")

        r00 = _row(rows, 0, 0)
        r11 = _row(rows, 1, 1)
        r22 = _row(rows, 2, 2)

        l1_00 = float(r00["l1_mean"])
        cos_00 = float(r00["cosine_loss_mean"])
        l1_11 = float(r11["l1_mean"])
        l1_22 = float(r22["l1_mean"])

        if l1_00 > 1e-8:
            raise AssertionError(f"expected zero-shift l1_mean ~= 0, got {l1_00}")
        if cos_00 > 1e-8:
            raise AssertionError(f"expected zero-shift cosine_loss_mean ~= 0, got {cos_00}")
        if l1_11 <= 0.0:
            raise AssertionError(f"expected non-zero shift to increase l1_mean, got {l1_11}")
        if l1_22 <= l1_11:
            raise AssertionError(f"expected larger shift to have larger l1_mean: {l1_22} <= {l1_11}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: analyze_phi_shift_sensitivity exports csv/png and expected monotonic trend")
