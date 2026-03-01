#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "viz_spatial_metrics_topk_frames.py"


def _write_concat_frame(path: Path, gt_value: int, pred_value: int, w: int = 8, h: int = 6) -> None:
    gt = np.full((h, w, 3), gt_value, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_viz_spatial_metrics_topk_frames_contract(tmp_path: Path) -> None:
    renders_a = tmp_path / "a"
    renders_b = tmp_path / "b"
    renders_a.mkdir(parents=True, exist_ok=True)
    renders_b.mkdir(parents=True, exist_ok=True)

    _write_concat_frame(renders_a / "test_step599_0000.png", gt_value=0, pred_value=10)
    _write_concat_frame(renders_a / "test_step599_0001.png", gt_value=0, pred_value=10)
    _write_concat_frame(renders_b / "test_step599_0000.png", gt_value=0, pred_value=11)
    _write_concat_frame(renders_b / "test_step599_0001.png", gt_value=0, pred_value=50)

    delta_csv = tmp_path / "delta.csv"
    with delta_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_idx", "delta_mae", "delta_psnr"])
        writer.writeheader()
        writer.writerow({"frame_idx": "0", "delta_mae": "0.0001", "delta_psnr": "0.0"})
        writer.writerow({"frame_idx": "1", "delta_mae": "0.0002", "delta_psnr": "0.0"})

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
    images = list(out_dir.glob("frame_*.jpg"))
    assert len(images) == 1
    assert images[0].name == "frame_0001.jpg"
