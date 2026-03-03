#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Row:
    frame_idx: int
    delta_mae: float
    delta_psnr: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export top-k frame snapshots for spatial metrics delta (planbfeat - planb)."
    )
    parser.add_argument(
        "--renders_dir_a",
        type=Path,
        required=True,
        help="planb_init_600 renders dir (GT|Pred concat).",
    )
    parser.add_argument(
        "--renders_dir_b",
        type=Path,
        required=True,
        help="planb_feat_v2_full600 renders dir (GT|Pred concat).",
    )
    parser.add_argument("--delta_csv", type=Path, required=True, help="spatial_metrics_delta_*.csv")
    parser.add_argument(
        "--out_dir",
        type=Path,
        required=True,
        help="Output directory under outputs/report_pack/diagnostics/.",
    )
    parser.add_argument(
        "--pattern_prefix",
        type=str,
        default="test_step599_",
        help="render filename prefix (default: test_step599_)",
    )
    parser.add_argument("--k", type=int, default=10, help="top-k frames by delta_mae desc")
    parser.add_argument("--resize_w", type=int, default=0, help="resize width (0 keeps original)")
    parser.add_argument("--quality", type=int, default=85, help="jpeg quality")
    return parser.parse_args()


def _load_gt_pred_concat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with Image.open(path) as image:
        image = image.convert("RGB")
        arr = np.asarray(image, dtype=np.float32) / 255.0
    _, w, _ = arr.shape
    if w % 2 != 0:
        raise ValueError(f"expected even width for GT|Pred concat, got w={w} for {path}")
    half = w // 2
    gt = arr[:, :half, :]
    pred = arr[:, half:, :]
    return gt, pred


def _to_u8(img_f: np.ndarray) -> Image.Image:
    x = np.clip(img_f * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(x)


def _err_u8(gt: np.ndarray, pred: np.ndarray) -> Image.Image:
    err = np.mean(np.abs(pred - gt), axis=2, keepdims=True)
    err = np.repeat(err, 3, axis=2)
    return _to_u8(err)


def _resize_keep_aspect(image: Image.Image, resize_w: int) -> Image.Image:
    if resize_w <= 0:
        return image
    w, h = image.size
    if w == resize_w:
        return image
    new_h = max(1, int(round(h * (resize_w / float(w)))))
    return image.resize((resize_w, new_h), resample=Image.BILINEAR)


def _read_rows(delta_csv: Path) -> list[Row]:
    rows: list[Row] = []
    with delta_csv.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            frame_idx = int(row["frame_idx"])
            delta_mae = float(row["delta_mae"])
            delta_psnr = row.get("delta_psnr", "")
            rows.append(
                Row(
                    frame_idx=frame_idx,
                    delta_mae=delta_mae,
                    delta_psnr=float(delta_psnr) if delta_psnr else None,
                )
            )
    if not rows:
        raise SystemExit(f"[ERROR] empty delta csv: {delta_csv}")
    return rows


def _render_path(renders_dir: Path, prefix: str, frame_idx: int) -> Path:
    return renders_dir / f"{prefix}{frame_idx:04d}.png"


def _write_readme(out_dir: Path, chosen: list[Row], delta_csv: Path) -> None:
    lines: list[str] = []
    lines.append("# spatial metrics top-k frame snapshots (planbfeat - planb) @ test_step599")
    lines.append("")
    lines.append(f"- delta csv: `{delta_csv}`")
    lines.append(f"- k: `{len(chosen)}` (sorted by `delta_mae` desc)")
    lines.append("")
    lines.append("| rank | frame_idx | delta_mae | delta_psnr | file |")
    lines.append("|---|---|---|---|---|")
    for rank, row in enumerate(chosen, 1):
        filename = f"frame_{row.frame_idx:04d}.jpg"
        delta_psnr = f"{row.delta_psnr:.8f}" if row.delta_psnr is not None else ""
        lines.append(f"| {rank} | {row.frame_idx} | {row.delta_mae:.8f} | {delta_psnr} | {filename} |")
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = _read_rows(args.delta_csv)
    rows_sorted = sorted(rows, key=lambda x: x.delta_mae, reverse=True)
    chosen = rows_sorted[: max(0, int(args.k))]

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for row in chosen:
        path_a = _render_path(args.renders_dir_a, args.pattern_prefix, row.frame_idx)
        path_b = _render_path(args.renders_dir_b, args.pattern_prefix, row.frame_idx)
        if not path_a.exists():
            raise SystemExit(f"[ERROR] missing frame in A: {path_a}")
        if not path_b.exists():
            raise SystemExit(f"[ERROR] missing frame in B: {path_b}")

        gt_a, pred_a = _load_gt_pred_concat(path_a)
        gt_b, pred_b = _load_gt_pred_concat(path_b)

        tiles = [
            _to_u8(gt_a),
            _to_u8(pred_a),
            _err_u8(gt_a, pred_a),
            _to_u8(gt_b),
            _to_u8(pred_b),
            _err_u8(gt_b, pred_b),
        ]
        tiles = [_resize_keep_aspect(tile, args.resize_w) for tile in tiles]

        tile_w, tile_h = tiles[0].size
        canvas = Image.new("RGB", (tile_w * 3, tile_h * 2), color=(0, 0, 0))
        for idx, tile in enumerate(tiles):
            x = (idx % 3) * tile_w
            y = (idx // 3) * tile_h
            canvas.paste(tile, (x, y))

        out_path = args.out_dir / f"frame_{row.frame_idx:04d}.jpg"
        canvas.save(out_path, quality=int(args.quality), optimize=True)

    _write_readme(args.out_dir, chosen, args.delta_csv)
    print(f"wrote {len(chosen)} frames to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
