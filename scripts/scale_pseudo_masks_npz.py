#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _fail(msg: str) -> None:
    raise SystemExit(f"[ScalePseudoMasks][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Scale uint8/float pseudo masks into float32 [0,1].")
    ap.add_argument("--in_npz", required=True)
    ap.add_argument("--out_npz", required=True)
    ap.add_argument(
        "--quantile", type=float, default=0.99, help="Global quantile for scaling (e.g. 0.99)"
    )
    ap.add_argument("--eps", type=float, default=1e-6)
    ap.add_argument(
        "--mode",
        choices=["dynamic_scaled", "static_from_dynamic_scaled"],
        default="dynamic_scaled",
    )
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def _load_required(npz: Path) -> tuple[np.ndarray, np.ndarray, int, int, int]:
    with np.load(npz, allow_pickle=True) as obj:
        required = ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale")
        missing = [k for k in required if k not in obj]
        if missing:
            _fail(f"npz missing keys: {missing}")
        masks = np.asarray(obj["masks"])
        cams = np.asarray(obj["camera_names"])
        frame_start = int(obj["frame_start"])
        num_frames = int(obj["num_frames"])
        down = int(obj["mask_downscale"])
    return masks, cams, frame_start, num_frames, down


def _to_float01(masks: np.ndarray) -> np.ndarray:
    if masks.dtype == np.uint8:
        return masks.astype(np.float32) / 255.0
    if masks.dtype in (np.float16, np.float32, np.float64):
        return np.clip(masks.astype(np.float32), 0.0, 1.0)
    _fail(f"unsupported masks dtype: {masks.dtype}")
    raise AssertionError


def main() -> int:
    args = parse_args()
    in_npz = Path(args.in_npz).resolve()
    out_npz = Path(args.out_npz).resolve()
    if not in_npz.exists():
        _fail(f"missing in_npz: {in_npz}")
    if out_npz.exists() and not args.overwrite:
        _fail(f"out_npz exists: {out_npz} (use --overwrite)")
    out_npz.parent.mkdir(parents=True, exist_ok=True)

    masks, cams, frame_start, num_frames, down = _load_required(in_npz)
    m01 = _to_float01(masks)
    if not (0.0 < args.quantile < 1.0):
        _fail(f"quantile must be in (0,1), got {args.quantile}")
    q = float(np.quantile(m01.reshape(-1), float(args.quantile)))
    denom = q + float(args.eps)
    if not np.isfinite(denom) or denom <= 0:
        _fail(f"invalid denom from quantile: q={q} eps={args.eps}")

    dyn = np.clip(m01 / denom, 0.0, 1.0).astype(np.float32)
    if args.mode == "dynamic_scaled":
        out_masks = dyn
        op = "dynamic_scaled"
    else:
        out_masks = (1.0 - dyn).astype(np.float32)
        op = "static_from_dynamic_scaled"

    np.savez_compressed(
        out_npz,
        masks=out_masks,
        camera_names=cams,
        frame_start=np.int32(int(frame_start)),
        num_frames=np.int32(int(num_frames)),
        mask_downscale=np.int32(int(down)),
        source_npz=str(in_npz),
        scale_quantile=np.float32(float(args.quantile)),
        scale_value=np.float32(float(q)),
        op=np.asarray([op], dtype=object),
    )
    print(f"[ScalePseudoMasks] wrote: {out_npz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
