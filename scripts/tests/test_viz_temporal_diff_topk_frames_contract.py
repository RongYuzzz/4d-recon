#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "viz_temporal_diff_topk_frames.py"


def _write_concat_frame(path: Path, pred_value: int, w: int = 8, h: int = 6) -> None:
    # Left half (GT) and right half (Pred) are concatenated horizontally.
    gt = np.full((h, w, 3), 20, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_viz_temporal_diff_topk_frames_contract(tmp_path: Path) -> None:
    renders_a = tmp_path / "a"
    renders_b = tmp_path / "b"
    renders_a.mkdir(parents=True, exist_ok=True)
    renders_b.mkdir(parents=True, exist_ok=True)

    # 3 frames for each run.
    for i, v in enumerate([10, 30, 50]):
        _write_concat_frame(renders_a / f"test_step599_{i:04d}.png", pred_value=v)
    for i, v in enumerate([10, 60, 90]):
        _write_concat_frame(renders_b / f"test_step599_{i:04d}.png", pred_value=v)

    # delta CSV: top-1 should pick pair (1,2).
    delta_csv = tmp_path / "delta.csv"
    with delta_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "pair_idx",
                "frame_prev",
                "frame_cur",
                "mean_abs_diff_a",
                "mean_abs_diff_b",
                "delta_mean_abs_diff",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "pair_idx": "0",
                "frame_prev": "0",
                "frame_cur": "1",
                "mean_abs_diff_a": "0.00000000",
                "mean_abs_diff_b": "0.00000000",
                "delta_mean_abs_diff": "0.00010000",
            }
        )
        w.writerow(
            {
                "pair_idx": "1",
                "frame_prev": "1",
                "frame_cur": "2",
                "mean_abs_diff_a": "0.00000000",
                "mean_abs_diff_b": "0.00000000",
                "delta_mean_abs_diff": "0.00020000",
            }
        )

    out_dir = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--renders_dir_a",
            str(renders_a),
            "--renders_dir_b",
            str(renders_b),
            "--delta_csv",
            str(delta_csv),
            "--out_dir",
            str(out_dir),
            "--k",
            "1",
            "--resize_w",
            "16",
            "--quality",
            "80",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, f"script failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert (out_dir / "README.md").exists()

    imgs = list(out_dir.glob("pair_*.jpg"))
    assert len(imgs) == 1, f"expected 1 output image, got {len(imgs)}"
    assert "0001_0002" in imgs[0].name
