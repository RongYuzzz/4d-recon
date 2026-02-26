#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_vggt_gate_framediff.py"


def _write_dummy_cache(npz_path: Path) -> None:
    # Shape: [T=2, V=3, 1, H=2, W=2]
    gate = np.array(
        [
            [
                [[[0.0, 0.0], [0.0, 0.0]]],
                [[[1.0, 1.0], [1.0, 1.0]]],
                [[[0.5, 0.5], [0.5, 0.5]]],
            ],
            [
                [[[0.2, 0.2], [0.2, 0.2]]],
                [[[0.8, 0.8], [0.8, 0.8]]],
                [[[0.4, 0.4], [0.4, 0.4]]],
            ],
        ],
        dtype=np.float32,
    )
    np.savez(npz_path, gate_framediff=gate)


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="gate_framediff_test_", dir=REPO_ROOT) as td:
        root = Path(td)
        cache_npz = root / "gt_cache.npz"
        out_dir = root / "outputs" / "report_pack" / "diagnostics"
        _write_dummy_cache(cache_npz)

        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--cache_npz",
                str(cache_npz),
                "--out_dir",
                str(out_dir),
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"analyze_vggt_gate_framediff failed:\n{proc.stdout}\n{proc.stderr}")

        by_frame_csv = out_dir / "gate_framediff_mean_by_frame.csv"
        by_view_csv = out_dir / "gate_framediff_mean_by_view.csv"
        heatmap_png = out_dir / "gate_framediff_heatmap.png"

        for p in (by_frame_csv, by_view_csv, heatmap_png):
            if not p.exists():
                raise AssertionError(f"missing expected output: {p}")

        frame_rows = list(csv.DictReader(by_frame_csv.open("r", encoding="utf-8", newline="")))
        view_rows = list(csv.DictReader(by_view_csv.open("r", encoding="utf-8", newline="")))
        if len(frame_rows) != 2:
            raise AssertionError(f"expected 2 frame rows, got {len(frame_rows)}")
        if len(view_rows) != 3:
            raise AssertionError(f"expected 3 view rows, got {len(view_rows)}")

        means_frame = [float(r["mean_gate"]) for r in frame_rows]
        means_view = [float(r["mean_gate"]) for r in view_rows]

        # Expected frame means: (0 + 1 + 0.5)/3 = 0.5, (0.2 + 0.8 + 0.4)/3 = 0.4666...
        if abs(means_frame[0] - 0.5) > 1e-6:
            raise AssertionError(f"unexpected frame0 mean: {means_frame[0]}")
        if abs(means_frame[1] - (1.4 / 3.0)) > 1e-6:
            raise AssertionError(f"unexpected frame1 mean: {means_frame[1]}")

        # View means across both frames.
        expected_view = [0.1, 0.9, 0.45]
        for idx, exp in enumerate(expected_view):
            if abs(means_view[idx] - exp) > 1e-6:
                raise AssertionError(f"unexpected view{idx} mean: {means_view[idx]} vs {exp}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: analyze_vggt_gate_framediff exports mean csv and heatmap")
