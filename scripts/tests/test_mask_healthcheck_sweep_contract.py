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
SCRIPT = REPO_ROOT / "scripts" / "mask_healthcheck_sweep.py"


def test_mask_healthcheck_emits_summary_json() -> None:
    with tempfile.TemporaryDirectory(prefix="mask_health_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        (data_dir / "masks" / cam).mkdir(parents=True, exist_ok=True)

        # GT: rectangle mask for 3 frames
        for t in range(3):
            arr = np.zeros((16, 20), dtype=np.uint8)
            arr[4:12, 6:14] = 255
            Image.fromarray(arr).save(data_dir / "masks" / cam / f"{t:06d}.png")

        # Pred: low-amplitude soft mask aligned with GT
        masks = np.zeros((3, 1, 4, 5), dtype=np.uint8)
        masks[:, 0, 1:3, 2:4] = 20  # small values
        pred_npz = root / "pred.npz"
        np.savez_compressed(
            pred_npz,
            masks=masks,
            camera_names=np.asarray([cam], dtype=object),
            frame_start=np.int32(0),
            num_frames=np.int32(3),
            mask_downscale=np.int32(4),
        )

        out_json = root / "out.json"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--pred_mask_npz",
            str(pred_npz),
            "--camera",
            cam,
            "--out_json",
            str(out_json),
            "--thr_pred_list",
            "0.01,0.05,0.10,0.50",
            "--top_p_list",
            "0.05,0.10",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == 0, f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
        obj = json.loads(out_json.read_text(encoding="utf-8"))
        for key in ("best_miou_fg", "best_thr_pred", "top_p_overlap"):
            assert key in obj
