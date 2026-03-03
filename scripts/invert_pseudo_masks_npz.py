#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def _fail(msg: str) -> None:
    raise SystemExit(f"[InvertPseudoMasks][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Invert uint8 pseudo masks in a cue_mining pseudo_masks.npz."
    )
    ap.add_argument("--in_npz", required=True, help="Input pseudo_masks.npz")
    ap.add_argument("--out_npz", required=True, help="Output npz path")
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    in_npz = Path(args.in_npz).resolve()
    out_npz = Path(args.out_npz).resolve()

    if not in_npz.exists():
        _fail(f"missing in_npz: {in_npz}")
    if out_npz.exists() and not args.overwrite:
        _fail(f"out_npz exists: {out_npz} (use --overwrite)")
    out_npz.parent.mkdir(parents=True, exist_ok=True)

    with np.load(in_npz, allow_pickle=True) as obj:
        missing = [
            k
            for k in ("masks", "camera_names", "frame_start", "num_frames", "mask_downscale")
            if k not in obj
        ]
        if missing:
            _fail(f"npz missing keys: {missing}")
        masks = np.asarray(obj["masks"])
        if masks.dtype != np.uint8:
            _fail(f"expected masks dtype=uint8, got {masks.dtype}")
        out_masks = (255 - masks).astype(np.uint8)

        np.savez_compressed(
            out_npz,
            masks=out_masks,
            camera_names=np.asarray(obj["camera_names"]),
            frame_start=np.int32(int(obj["frame_start"])),
            num_frames=np.int32(int(obj["num_frames"])),
            mask_downscale=np.int32(int(obj["mask_downscale"])),
        )

    print(f"[InvertPseudoMasks] wrote: {out_npz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

