#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export composite frame snapshots for temporal-diff top-k pairs.")
    p.add_argument("--renders_dir_a", type=Path, required=True, help="Renders dir for planb_init_600 (GT|Pred concat).")
    p.add_argument(
        "--renders_dir_b",
        type=Path,
        required=True,
        help="Renders dir for planb_feat_v2_full600 (GT|Pred concat).",
    )
    p.add_argument("--delta_csv", type=Path, required=True, help="temporal_diff_delta_*.csv (planbfeat - planb).")
    p.add_argument("--out_dir", type=Path, required=True, help="Output directory under outputs/report_pack/diagnostics/.")
    p.add_argument("--pattern_prefix", type=str, default="test_step599_", help="Filename prefix (default: test_step599_).")
    p.add_argument("--k", type=int, default=10, help="Top-k pairs to export (default: 10).")
    p.add_argument("--resize_w", type=int, default=640, help="Resize Pred-half tiles to this width (default: 640).")
    p.add_argument("--quality", type=int, default=85, help="JPEG quality (default: 85).")
    return p.parse_args()


def _pred_half(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if w % 2 != 0:
        raise ValueError(f"expected even width for gt|pred concat: {path} ({w})")
    mid = w // 2
    return img.crop((mid, 0, w, h))


def _resize_to_w(img: Image.Image, w: int) -> Image.Image:
    if w <= 0:
        raise ValueError("resize_w must be > 0")
    ow, oh = img.size
    if ow == w:
        return img
    nh = max(1, int(round(oh * (w / float(ow)))))
    return img.resize((w, nh), resample=Image.BILINEAR)


def _absdiff_vis(a: Image.Image, b: Image.Image) -> Image.Image:
    # Visualize absdiff(a, b) as grayscale (auto-scaled by p99) for audit.
    aa = np.asarray(a, dtype=np.float32)
    bb = np.asarray(b, dtype=np.float32)
    if aa.shape != bb.shape:
        raise ValueError(f"shape mismatch: {aa.shape} vs {bb.shape}")
    d = np.abs(aa - bb).mean(axis=2)  # [H,W], 0..255
    p99 = float(np.percentile(d, 99.0))
    scale = 255.0 / max(p99, 1e-6)
    dv = np.clip(d * scale, 0.0, 255.0).astype(np.uint8)
    return Image.fromarray(dv, mode="L").convert("RGB")


def _composite(a_prev: Image.Image, a_cur: Image.Image, b_prev: Image.Image, b_cur: Image.Image) -> Image.Image:
    # 2 rows (A,B) x 3 cols (prev,cur,diff)
    pad = 6
    a_diff = _absdiff_vis(a_prev, a_cur)
    b_diff = _absdiff_vis(b_prev, b_cur)

    tiles = [
        [a_prev, a_cur, a_diff],
        [b_prev, b_cur, b_diff],
    ]
    tile_w, tile_h = tiles[0][0].size
    canvas_w = pad + 3 * (tile_w + pad)
    canvas_h = pad + 2 * (tile_h + pad)
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(16, 16, 16))

    for r in range(2):
        for c in range(3):
            x = pad + c * (tile_w + pad)
            y = pad + r * (tile_h + pad)
            canvas.paste(tiles[r][c], (x, y))
    return canvas


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(args.delta_csv.open(newline="", encoding="utf-8")))
    if not rows:
        raise SystemExit(f"empty delta_csv: {args.delta_csv}")

    # Sort by delta desc; take top-k.
    rows_sorted = sorted(rows, key=lambda r: float(r["delta_mean_abs_diff"]), reverse=True)
    rows_top = rows_sorted[: max(0, int(args.k))]

    readme_lines = [
        "# Temporal Diff Top-k Frame Snapshots (Pred half)",
        "",
        f"- delta_csv: `{args.delta_csv}`",
        "",
        "| rank | frame_prev | frame_cur | delta_mean_abs_diff | image |",
        "| ---: | ---: | ---: | ---: | --- |",
    ]

    for rank, r in enumerate(rows_top, 1):
        fp = int(r["frame_prev"])
        fc = int(r["frame_cur"])
        delta = float(r["delta_mean_abs_diff"])

        pa_prev = args.renders_dir_a / f"{args.pattern_prefix}{fp:04d}.png"
        pa_cur = args.renders_dir_a / f"{args.pattern_prefix}{fc:04d}.png"
        pb_prev = args.renders_dir_b / f"{args.pattern_prefix}{fp:04d}.png"
        pb_cur = args.renders_dir_b / f"{args.pattern_prefix}{fc:04d}.png"

        a_prev = _resize_to_w(_pred_half(pa_prev), args.resize_w)
        a_cur = _resize_to_w(_pred_half(pa_cur), args.resize_w)
        b_prev = _resize_to_w(_pred_half(pb_prev), args.resize_w)
        b_cur = _resize_to_w(_pred_half(pb_cur), args.resize_w)

        out_name = f"pair_{fp:04d}_{fc:04d}.jpg"
        out_path = args.out_dir / out_name
        comp = _composite(a_prev, a_cur, b_prev, b_cur)
        comp.save(out_path, quality=int(args.quality), optimize=True)

        readme_lines.append(f"| {rank} | {fp} | {fc} | {delta:.8f} | `{out_name}` |")

    (args.out_dir / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out_dir} ({len(rows_top)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
