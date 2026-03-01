#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute per-pair tLPIPS curve from render frames (GT|Pred concat)."
    )
    parser.add_argument("--renders_dir", type=Path, required=True, help="Directory containing render PNG files.")
    parser.add_argument(
        "--pattern_prefix",
        type=str,
        default="test_step599_",
        help="Filename prefix before frame index (e.g. test_step599_).",
    )
    parser.add_argument("--out_csv", type=Path, required=True, help="Output CSV path.")
    parser.add_argument("--device", type=str, default="cpu", help="Torch device for LPIPS calculation.")
    return parser.parse_args()


def _frame_index_from_name(path: Path, prefix: str) -> int:
    m = re.fullmatch(rf"{re.escape(prefix)}(\d+)\.png", path.name)
    if m is None:
        raise ValueError(f"filename does not match expected pattern: {path.name!r}")
    return int(m.group(1))


def _extract_pred_half(image_path: Path) -> np.ndarray:
    img = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.float32) / 255.0
    h, w, _ = img.shape
    if w % 2 != 0:
        raise ValueError(f"expected even image width for gt|pred concat, got {w} ({image_path})")
    mid = w // 2
    pred = img[:, mid:, :]
    assert pred.shape[0] == h and pred.shape[1] == mid
    return pred


def find_frames(renders_dir: Path, pattern_prefix: str) -> list[Path]:
    candidates = sorted(renders_dir.glob(f"{pattern_prefix}*.png"))
    frames: list[tuple[int, Path]] = []
    for p in candidates:
        try:
            idx = _frame_index_from_name(p, pattern_prefix)
        except ValueError:
            continue
        frames.append((idx, p))
    frames.sort(key=lambda x: x[0])
    return [p for _, p in frames]


def _to_tensor(img: np.ndarray, device: str) -> torch.Tensor:
    t = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).contiguous()
    return t.to(device=device, dtype=torch.float32)


def compute_tlpips_rows(frames: list[Path], pattern_prefix: str, device: str) -> list[dict[str, str]]:
    if len(frames) < 2:
        raise ValueError(f"need at least 2 frames, got {len(frames)}")

    pred_frames = [_extract_pred_half(p) for p in frames]
    frame_indices = [_frame_index_from_name(p, pattern_prefix) for p in frames]

    metric = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True).to(device)
    metric.eval()

    rows: list[dict[str, str]] = []
    with torch.no_grad():
        for pair_idx in range(1, len(pred_frames)):
            prev = _to_tensor(pred_frames[pair_idx - 1], device=device)
            cur = _to_tensor(pred_frames[pair_idx], device=device)
            metric.update(cur, prev)
            tlpips = float(metric.compute().detach().cpu().item())
            metric.reset()
            rows.append(
                {
                    "pair_idx": str(pair_idx - 1),
                    "frame_prev": str(frame_indices[pair_idx - 1]),
                    "frame_cur": str(frame_indices[pair_idx]),
                    "tlpips": f"{tlpips:.8f}",
                }
            )
    return rows


def write_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["pair_idx", "frame_prev", "frame_cur", "tlpips"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    args = parse_args()
    frames = find_frames(args.renders_dir, args.pattern_prefix)
    rows = compute_tlpips_rows(frames, args.pattern_prefix, args.device)
    write_csv(rows, args.out_csv)
    print(f"wrote {args.out_csv}")


if __name__ == "__main__":
    main()
