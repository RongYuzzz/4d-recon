#!/usr/bin/env python3
"""Analyze gate_framediff activation statistics from gt_cache.npz."""

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


def _load_gate(cache_npz: Path) -> np.ndarray:
    if not cache_npz.exists():
        raise FileNotFoundError(f"cache npz missing: {cache_npz}")
    data = np.load(cache_npz, allow_pickle=False)
    if "gate_framediff" not in data.files:
        raise KeyError(f"'gate_framediff' missing in npz keys={data.files}")
    gate = np.asarray(data["gate_framediff"], dtype=np.float32)
    if gate.ndim == 5 and gate.shape[2] == 1:
        gate = gate[:, :, 0, :, :]
    if gate.ndim != 4:
        raise ValueError(f"gate_framediff must be [T,V,Hf,Wf] or [T,V,1,Hf,Wf], got shape={gate.shape}")
    return gate


def _write_frame_csv(path: Path, mean_by_frame: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["frame_idx", "mean_gate"])
        writer.writeheader()
        for idx, value in enumerate(mean_by_frame.tolist()):
            writer.writerow({"frame_idx": idx, "mean_gate": f"{float(value):.9g}"})


def _write_view_csv(path: Path, mean_by_view: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["view_idx", "mean_gate"])
        writer.writeheader()
        for idx, value in enumerate(mean_by_view.tolist()):
            writer.writerow({"view_idx": idx, "mean_gate": f"{float(value):.9g}"})


def _write_heatmap(path: Path, frame_view_mean: np.ndarray) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(frame_view_mean, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_title("gate_framediff Mean Activation (Frame x View)")
    ax.set_xlabel("view_idx")
    ax.set_ylabel("frame_idx")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("mean_gate")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache_npz", required=True, help="Path to gt_cache.npz containing gate_framediff")
    parser.add_argument("--out_dir", default="outputs/report_pack/diagnostics")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cache_npz = _resolve_path(args.cache_npz)
    out_dir = _resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gate = _load_gate(cache_npz)
    # frame_view_mean: [T, V]
    frame_view_mean = gate.mean(axis=(2, 3))
    mean_by_frame = frame_view_mean.mean(axis=1)
    mean_by_view = frame_view_mean.mean(axis=0)

    frame_csv = out_dir / "gate_framediff_mean_by_frame.csv"
    view_csv = out_dir / "gate_framediff_mean_by_view.csv"
    heatmap_png = out_dir / "gate_framediff_heatmap.png"

    _write_frame_csv(frame_csv, mean_by_frame)
    _write_view_csv(view_csv, mean_by_view)
    _write_heatmap(heatmap_png, frame_view_mean)

    print(f"wrote {frame_csv}")
    print(f"wrote {view_csv}")
    print(f"wrote {heatmap_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
