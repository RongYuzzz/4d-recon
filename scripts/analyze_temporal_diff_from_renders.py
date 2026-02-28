#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute temporal-diff time-series from render frames (GT|Pred concat)."
    )
    parser.add_argument("--renders_dir", type=Path, required=True, help="Directory containing render PNG files.")
    parser.add_argument(
        "--pattern_prefix",
        type=str,
        default="test_step599_",
        help="Filename prefix before frame index (e.g. test_step599_).",
    )
    parser.add_argument("--out_csv", type=Path, required=True, help="Output CSV path.")
    parser.add_argument(
        "--split_mode",
        type=str,
        default="gt_pred_concat",
        choices=["gt_pred_concat"],
        help="How to split render image to extract Pred half.",
    )
    return parser.parse_args()


def _frame_index_from_name(path: Path, prefix: str) -> int:
    m = re.fullmatch(rf"{re.escape(prefix)}(\d+)\.png", path.name)
    if m is None:
        raise ValueError(f"filename does not match expected pattern: {path.name!r}")
    return int(m.group(1))


def _extract_pred_half(image_path: Path, split_mode: str) -> np.ndarray:
    img = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.float32) / 255.0
    if split_mode != "gt_pred_concat":
        raise ValueError(f"unsupported split_mode: {split_mode}")

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


def compute_temporal_diff_rows(frames: list[Path], split_mode: str, pattern_prefix: str) -> list[dict[str, str]]:
    if len(frames) < 2:
        raise ValueError(f"need at least 2 frames, got {len(frames)}")

    pred_frames = [_extract_pred_half(p, split_mode) for p in frames]
    frame_indices = [_frame_index_from_name(p, pattern_prefix) for p in frames]

    rows: list[dict[str, str]] = []
    for pair_idx in range(1, len(pred_frames)):
        prev = pred_frames[pair_idx - 1]
        cur = pred_frames[pair_idx]
        if prev.shape != cur.shape:
            raise ValueError(f"shape mismatch at pair {pair_idx}: {prev.shape} vs {cur.shape}")
        mad = float(np.abs(cur - prev).mean())
        rows.append(
            {
                "pair_idx": str(pair_idx - 1),
                "frame_prev": str(frame_indices[pair_idx - 1]),
                "frame_cur": str(frame_indices[pair_idx]),
                "mean_abs_diff": f"{mad:.8f}",
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["pair_idx", "frame_prev", "frame_cur", "mean_abs_diff"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    args = parse_args()
    frames = find_frames(args.renders_dir, args.pattern_prefix)
    rows = compute_temporal_diff_rows(frames, args.split_mode, args.pattern_prefix)
    write_csv(rows, args.out_csv)
    print(f"wrote {args.out_csv}")


if __name__ == "__main__":
    main()
