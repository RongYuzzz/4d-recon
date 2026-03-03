#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _fail(msg: str) -> None:
    raise SystemExit(f"[THUman4Inventory][ERROR] {msg}")


def _list_cams(root: Path) -> list[str]:
    images = root / "images"
    masks = root / "masks"
    if not images.is_dir():
        _fail(f"missing images/: {images}")
    if not masks.is_dir():
        _fail(f"missing masks/: {masks}")
    img_cams = sorted(path.name for path in images.iterdir() if path.is_dir())
    msk_cams = sorted(path.name for path in masks.iterdir() if path.is_dir())
    cams = sorted(set(img_cams).intersection(msk_cams))
    if not cams:
        _fail("no common camera dirs between images/ and masks/")
    return cams


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan THUman4.0 subject directory and emit an adapter command."
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="THUman subject dir containing images/ and masks/",
    )
    parser.add_argument("--num_cams", type=int, default=8)
    parser.add_argument("--num_frames", type=int, default=60)
    parser.add_argument("--frame_start", type=int, default=0)
    parser.add_argument("--image_downscale", type=int, default=2)
    parser.add_argument(
        "--output_camera_ids",
        default="02,03,04,05,06,07,08,09",
        help="Default FreeTime camera ids for 8-cam subset",
    )
    parser.add_argument(
        "--output_dir",
        default="data/thuman4_subject00_8cam60f",
        help="Default output dir under repo data/ (local-eval only)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    cams = _list_cams(input_dir)

    num_cams = int(args.num_cams)
    if num_cams <= 0:
        _fail("--num_cams must be > 0")
    if len(cams) < num_cams:
        _fail(f"not enough cameras: detected={len(cams)} need={num_cams}")
    picked = cams[:num_cams]

    payload = {
        "input_dir": str(input_dir),
        "detected_cameras": cams,
        "picked_cameras": picked,
        "frame_start": int(args.frame_start),
        "num_frames": int(args.num_frames),
        "image_downscale": int(args.image_downscale),
        "output_dir": str(args.output_dir),
        "output_camera_ids": str(args.output_camera_ids),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("")
    print("# Suggested adapter command (local-eval only):")
    print("python3 scripts/adapt_thuman4_release_to_freetime.py \\")
    print(f"  --input_dir '{input_dir}' \\")
    print(f"  --output_dir '{args.output_dir}' \\")
    print(f"  --camera_ids '{','.join(picked)}' \\")
    print(f"  --output_camera_ids '{args.output_camera_ids}' \\")
    print(f"  --frame_start {int(args.frame_start)} \\")
    print(f"  --num_frames {int(args.num_frames)} \\")
    print(f"  --image_downscale {int(args.image_downscale)} \\")
    print("  --overwrite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

