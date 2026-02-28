#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_temporal_diff_from_renders.py"


def _write_concat_frame(path: Path, pred_value: int, w: int = 6, h: int = 4) -> None:
    # Left half (GT) and right half (Pred) are concatenated horizontally.
    gt = np.full((h, w, 3), 90, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_temporal_diff_from_renders_contract(tmp_path: Path) -> None:
    renders_dir = tmp_path / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)

    _write_concat_frame(renders_dir / "test_step599_0000.png", pred_value=20)
    _write_concat_frame(renders_dir / "test_step599_0001.png", pred_value=80)
    _write_concat_frame(renders_dir / "test_step599_0002.png", pred_value=140)

    out_csv = tmp_path / "temporal_diff.csv"

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--renders_dir",
            str(renders_dir),
            "--pattern_prefix",
            "test_step599_",
            "--out_csv",
            str(out_csv),
            "--split_mode",
            "gt_pred_concat",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"script failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert out_csv.exists(), "expected out_csv to be created"

    rows = list(csv.DictReader(out_csv.open("r", newline="", encoding="utf-8")))
    assert len(rows) == 2, f"expected 2 pair rows, got {len(rows)}"
    assert rows, "csv should contain at least one row"

    required_cols = {"pair_idx", "frame_prev", "frame_cur", "mean_abs_diff"}
    assert required_cols.issubset(rows[0].keys()), f"missing required cols in csv: {rows[0].keys()}"
