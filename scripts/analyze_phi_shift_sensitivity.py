#!/usr/bin/env python3
"""Analyze phi-space shift sensitivity from cached phi tensor."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def _load_phi(cache_npz: Path) -> np.ndarray:
    if not cache_npz.exists():
        raise FileNotFoundError(f"cache npz missing: {cache_npz}")
    data = np.load(cache_npz, allow_pickle=False)
    if "phi" not in data.files:
        raise KeyError(f"'phi' missing in npz keys={data.files}")
    phi = np.asarray(data["phi"], dtype=np.float32)
    if phi.ndim != 5:
        raise ValueError(f"phi must be [T,V,C,Hf,Wf], got shape={phi.shape}")
    return phi


def _shift_spatial_zero_pad(phi: np.ndarray, dx: int, dy: int) -> np.ndarray:
    # phi: [T,V,C,H,W], shift in x/y with zero fill.
    out = np.zeros_like(phi)
    _, _, _, h, w = phi.shape

    if dx >= 0:
        src_x0, src_x1 = 0, w - dx
        dst_x0, dst_x1 = dx, w
    else:
        src_x0, src_x1 = -dx, w
        dst_x0, dst_x1 = 0, w + dx

    if dy >= 0:
        src_y0, src_y1 = 0, h - dy
        dst_y0, dst_y1 = dy, h
    else:
        src_y0, src_y1 = -dy, h
        dst_y0, dst_y1 = 0, h + dy

    if src_x1 <= src_x0 or src_y1 <= src_y0:
        return out
    out[:, :, :, dst_y0:dst_y1, dst_x0:dst_x1] = phi[:, :, :, src_y0:src_y1, src_x0:src_x1]
    return out


def _compute_losses(phi_ref: np.ndarray, phi_shifted: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Flatten channel dim for per-position cosine, output shape [N] where N=T*V*H*W
    ref = np.moveaxis(phi_ref, 2, -1).reshape(-1, phi_ref.shape[2])
    shf = np.moveaxis(phi_shifted, 2, -1).reshape(-1, phi_shifted.shape[2])

    ref_norm = np.linalg.norm(ref, axis=1)
    shf_norm = np.linalg.norm(shf, axis=1)
    denom = np.clip(ref_norm * shf_norm, 1e-12, None)
    cosine = np.sum(ref * shf, axis=1) / denom
    cosine = np.clip(cosine, -1.0, 1.0)
    cosine_loss = 1.0 - cosine
    # Treat both-zero vectors as no change.
    both_zero = (ref_norm < 1e-12) & (shf_norm < 1e-12)
    cosine_loss[both_zero] = 0.0

    l1 = np.mean(np.abs(ref - shf), axis=1)
    return cosine_loss, l1


def _write_csv(path: Path, rows: list[dict[str, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dx",
                "dy",
                "cosine_loss_mean",
                "cosine_loss_p90",
                "l1_mean",
                "l1_p90",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "dx": int(row["dx"]),
                    "dy": int(row["dy"]),
                    "cosine_loss_mean": f"{row['cosine_loss_mean']:.9g}",
                    "cosine_loss_p90": f"{row['cosine_loss_p90']:.9g}",
                    "l1_mean": f"{row['l1_mean']:.9g}",
                    "l1_p90": f"{row['l1_p90']:.9g}",
                }
            )


def _write_plot(path: Path, grid: np.ndarray, title: str) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(grid, cmap="magma", origin="lower")
    ax.set_title(title)
    ax.set_xlabel("dx index")
    ax.set_ylabel("dy index")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("mean loss")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache_npz", required=True, help="Path to gt_cache.npz containing phi")
    parser.add_argument("--out_dir", default="outputs/report_pack/diagnostics")
    parser.add_argument("--max_shift", type=int, default=2, help="Evaluate dx/dy in [-max_shift, max_shift]")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_shift < 0:
        raise ValueError("--max_shift must be >= 0")

    cache_npz = _resolve_path(args.cache_npz)
    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    phi = _load_phi(cache_npz)

    shifts = list(range(-args.max_shift, args.max_shift + 1))
    rows: list[dict[str, float]] = []
    l1_grid = np.zeros((len(shifts), len(shifts)), dtype=np.float32)

    for yi, dy in enumerate(shifts):
        for xi, dx in enumerate(shifts):
            shifted = _shift_spatial_zero_pad(phi, dx=dx, dy=dy)
            cos_loss, l1 = _compute_losses(phi, shifted)
            row = {
                "dx": float(dx),
                "dy": float(dy),
                "cosine_loss_mean": float(np.mean(cos_loss)),
                "cosine_loss_p90": float(np.percentile(cos_loss, 90)),
                "l1_mean": float(np.mean(l1)),
                "l1_p90": float(np.percentile(l1, 90)),
            }
            rows.append(row)
            l1_grid[yi, xi] = row["l1_mean"]

    out_csv = out_dir / "phi_shift_sensitivity.csv"
    out_png = out_dir / "phi_shift_sensitivity.png"
    _write_csv(out_csv, rows)
    _write_plot(out_png, l1_grid, title="phi-space shift sensitivity (L1 mean)")

    print(f"wrote {out_csv}")
    print(f"wrote {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
