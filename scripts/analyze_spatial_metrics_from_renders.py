#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


FRAME_SUFFIX = re.compile(r"_(\d+)\.png$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute per-frame spatial metrics (GT vs Pred) from concat renders (GT|Pred)."
    )
    parser.add_argument("--renders_dir", type=Path, required=True, help="Directory containing renders.")
    parser.add_argument("--pattern_prefix", type=str, default="test_step599_", help="Filename prefix to match frames.")
    parser.add_argument("--out_csv", type=Path, required=True, help="Output CSV path.")
    parser.add_argument("--with_lpips", action="store_true", help="Also compute LPIPS(alex, normalize=True) per-frame.")
    parser.add_argument("--device", type=str, default="cuda", help="Torch device for LPIPS (e.g. cuda/cpu).")
    return parser.parse_args()


def _frame_idx_from_name(name: str) -> int:
    matched = FRAME_SUFFIX.search(name)
    if not matched:
        raise ValueError(f"cannot parse frame idx from filename: {name}")
    return int(matched.group(1))


def _load_gt_pred_concat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    image = Image.open(path).convert("RGB")
    array = np.asarray(image, dtype=np.float32) / 255.0
    _, width, _ = array.shape
    if width % 2 != 0:
        raise ValueError(f"expected even width for GT|Pred concat, got w={width} for {path}")
    half_width = width // 2
    gt = array[:, :half_width, :]
    pred = array[:, half_width:, :]
    return gt, pred


def _compute_mae_mse_psnr(gt: np.ndarray, pred: np.ndarray) -> tuple[float, float, float]:
    diff = pred - gt
    mae = float(np.mean(np.abs(diff)))
    mse = float(np.mean(diff * diff))
    if mse == 0.0:
        psnr = float("inf")
    else:
        psnr = 10.0 * math.log10(1.0 / mse)
    return mae, mse, psnr


def _lpips_metric(device: str):
    import torch
    from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity

    metric = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True)
    metric = metric.to(device)
    metric.eval()
    return torch, metric


def main() -> int:
    args = parse_args()
    renders_dir: Path = args.renders_dir
    out_csv: Path = args.out_csv
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    frame_paths = [path for path in renders_dir.glob(f"{args.pattern_prefix}*.png") if path.is_file()]
    if not frame_paths:
        raise SystemExit(f"[ERROR] no frames matched in {renders_dir} with prefix {args.pattern_prefix!r}")
    frame_paths = sorted(frame_paths, key=lambda path: _frame_idx_from_name(path.name))

    want_lpips = bool(args.with_lpips)
    torch = None
    lpips = None
    if want_lpips:
        torch, lpips = _lpips_metric(args.device)

    fieldnames = ["frame_idx", "mae", "mse", "psnr"] + (["lpips"] if want_lpips else [])
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for path in frame_paths:
            frame_idx = _frame_idx_from_name(path.name)
            gt, pred = _load_gt_pred_concat(path)
            mae, mse, psnr = _compute_mae_mse_psnr(gt, pred)

            row: dict[str, Any] = {
                "frame_idx": str(frame_idx),
                "mae": f"{mae:.8f}",
                "mse": f"{mse:.8f}",
                "psnr": f"{psnr:.8f}" if math.isfinite(psnr) else "inf",
            }

            if want_lpips:
                assert torch is not None and lpips is not None
                with torch.no_grad():
                    gt_tensor = torch.from_numpy(gt).permute(2, 0, 1).unsqueeze(0).to(args.device)
                    pred_tensor = torch.from_numpy(pred).permute(2, 0, 1).unsqueeze(0).to(args.device)
                    row["lpips"] = f"{float(lpips(pred_tensor, gt_tensor).item()):.8f}"

            writer.writerow(row)

    print(f"wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
