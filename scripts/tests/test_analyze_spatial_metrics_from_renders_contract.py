#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_spatial_metrics_from_renders.py"


def _write_concat_frame(path: Path, gt_value: int, pred_value: int, w: int = 8, h: int = 6) -> None:
    gt = np.full((h, w, 3), gt_value, dtype=np.uint8)
    pred = np.full((h, w, 3), pred_value, dtype=np.uint8)
    img = np.concatenate([gt, pred], axis=1)
    Image.fromarray(img).save(path)


def test_analyze_spatial_metrics_from_renders_contract(tmp_path: Path) -> None:
    renders = tmp_path / "renders"
    renders.mkdir(parents=True, exist_ok=True)

    _write_concat_frame(renders / "test_step599_0000.png", gt_value=0, pred_value=255)
    _write_concat_frame(renders / "test_step599_0001.png", gt_value=0, pred_value=127)

    out_csv = tmp_path / "out.csv"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--renders_dir",
            str(renders),
            "--pattern_prefix",
            "test_step599_",
            "--out_csv",
            str(out_csv),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"script failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert out_csv.exists()

    rows = list(csv.DictReader(out_csv.open(newline="", encoding="utf-8")))
    assert [r["frame_idx"] for r in rows] == ["0", "1"]
    assert set(rows[0].keys()) == {"frame_idx", "mae", "mse", "psnr"}

    mae0 = float(rows[0]["mae"])
    mse0 = float(rows[0]["mse"])
    psnr0 = float(rows[0]["psnr"])
    assert abs(mae0 - 1.0) < 1e-7
    assert abs(mse0 - 1.0) < 1e-7
    assert abs(psnr0 - 0.0) < 1e-7

    d1 = 127.0 / 255.0
    mae1 = float(rows[1]["mae"])
    mse1 = float(rows[1]["mse"])
    psnr1 = float(rows[1]["psnr"])
    assert abs(mae1 - d1) < 1e-6
    assert abs(mse1 - (d1 * d1)) < 1e-6
    exp_psnr1 = 10.0 * math.log10(1.0 / (d1 * d1))
    assert abs(psnr1 - exp_psnr1) < 1e-5
