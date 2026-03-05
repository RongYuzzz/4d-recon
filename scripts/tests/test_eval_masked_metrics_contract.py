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
SCRIPT = REPO_ROOT / "scripts" / "eval_masked_metrics.py"


def _write_rgb(path: Path, seed: int) -> None:
    rng = np.random.default_rng(seed)
    arr = (rng.random((32, 40, 3)) * 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def _write_mask(path: Path) -> None:
    arr = np.zeros((32, 40), dtype=np.uint8)
    arr[8:24, 10:30] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def _write_canvas_concat_gt_pred(path: Path, seed_gt: int, seed_pred: int) -> None:
    rng_gt = np.random.default_rng(seed_gt)
    rng_pd = np.random.default_rng(seed_pred)
    gt = (rng_gt.random((32, 40, 3)) * 255).astype(np.uint8)
    pred = (rng_pd.random((32, 40, 3)) * 255).astype(np.uint8)
    canvas = np.concatenate([gt, pred], axis=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(canvas).save(path)


def test_eval_masked_metrics_emits_required_fields() -> None:
    with tempfile.TemporaryDirectory(prefix="eval_masked_metrics_") as td:
        root = Path(td)
        data_dir = root / "data_scene"
        cam = "09"
        for t in range(3):
            _write_rgb(data_dir / "images" / cam / f"{t:06d}.jpg", seed=100 + t)
            _write_mask(data_dir / "masks" / cam / f"{t:06d}.png")

        result_dir = root / "run"
        (result_dir / "stats").mkdir(parents=True, exist_ok=True)
        (result_dir / "renders").mkdir(parents=True, exist_ok=True)
        (result_dir / "cfg.yml").write_text(
            "\n".join(
                [
                    "start_frame: 0",
                    "end_frame: 3",
                    f"test_camera_names: {cam}",
                    "eval_sample_every_test: 1",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (result_dir / "stats" / "test_step0599.json").write_text(
            json.dumps({"psnr": 1.0, "ssim": 0.1, "lpips": 0.9, "tlpips": 0.01}) + "\n",
            encoding="utf-8",
        )
        for i in range(3):
            _write_canvas_concat_gt_pred(
                result_dir / "renders" / f"test_step599_{i:04d}.png",
                seed_gt=200 + i,
                seed_pred=300 + i,
            )

        out_json = result_dir / "stats_masked" / "test_step0599.json"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--data_dir",
            str(data_dir),
            "--result_dir",
            str(result_dir),
            "--stage",
            "test",
            "--step",
            "599",
            "--mask_source",
            "dataset",
            "--bbox_margin_px",
            "4",
            "--lpips_backend",
            "dummy",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
        assert out_json.exists()

        obj = json.loads(out_json.read_text(encoding="utf-8"))
        for key in (
            "psnr",
            "ssim",
            "lpips",
            "tlpips",
            "psnr_fg",
            "lpips_fg",
            "psnr_fg_area",
            "lpips_fg_comp",
            "lpips_backend",
            "mask_source",
        ):
            assert key in obj, f"missing key: {key}"
        assert obj["lpips_backend"] in ("auto", "dummy", "none")
        assert obj["mask_source"] == "dataset"
        assert obj["num_fg_frames"] > 0
