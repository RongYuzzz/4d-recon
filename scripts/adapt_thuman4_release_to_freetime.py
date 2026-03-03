#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[THUman4Adapter][ERROR] {msg}")


def _parse_csv_list(raw: str) -> list[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    if not items:
        _fail("empty list")
    return items


def _index_numeric_frames(dir_path: Path) -> dict[int, Path]:
    frame_map: dict[int, Path] = {}
    if not dir_path.is_dir():
        _fail(f"missing dir: {dir_path}")
    for path in dir_path.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        try:
            frame_idx = int(path.stem)
        except ValueError:
            continue
        frame_map[frame_idx] = path
    return frame_map


def _resize_rgb(im: Image.Image, downscale: int) -> Image.Image:
    if downscale <= 1:
        return im
    width, height = im.size
    out_width = max(1, width // downscale)
    out_height = max(1, height // downscale)
    return im.resize((out_width, out_height), resample=Image.Resampling.BILINEAR)


def _resize_mask(im: Image.Image, downscale: int) -> Image.Image:
    if downscale <= 1:
        return im
    width, height = im.size
    out_width = max(1, width // downscale)
    out_height = max(1, height // downscale)
    return im.resize((out_width, out_height), resample=Image.Resampling.NEAREST)


@dataclass(frozen=True)
class ManifestRow:
    input_cam: str
    output_cam: str
    input_frame: int
    output_frame: int
    input_image: str
    output_image: str
    input_mask: str
    output_mask: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adapt THUman4.0 subject to FreeTime-compatible layout (local-eval only)."
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="THUman subject dir (expects images/ and masks/)",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Output data dir under repo data/",
    )
    parser.add_argument(
        "--camera_ids",
        required=True,
        help="Comma-separated input camera folder names",
    )
    parser.add_argument(
        "--output_camera_ids",
        required=True,
        help="Comma-separated output camera ids (same length)",
    )
    parser.add_argument("--frame_start", type=int, default=0)
    parser.add_argument("--num_frames", type=int, default=60)
    parser.add_argument("--image_downscale", type=int, default=2)
    parser.add_argument("--copy_mode", choices=["copy"], default="copy")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    if output_dir.exists() and not args.overwrite:
        _fail(f"output_dir exists (use --overwrite): {output_dir}")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    in_cams = _parse_csv_list(args.camera_ids)
    out_cams = _parse_csv_list(args.output_camera_ids)
    if len(in_cams) != len(out_cams):
        _fail(f"camera_ids length mismatch: {len(in_cams)} vs {len(out_cams)}")

    frame_start = int(args.frame_start)
    num_frames = int(args.num_frames)
    if num_frames <= 0:
        _fail("num_frames must be > 0")
    image_downscale = int(args.image_downscale)
    if image_downscale <= 0:
        _fail("image_downscale must be >= 1")

    images_in_root = input_dir / "images"
    masks_in_root = input_dir / "masks"
    if not images_in_root.is_dir():
        _fail(f"missing images/: {images_in_root}")
    if not masks_in_root.is_dir():
        _fail(f"missing masks/: {masks_in_root}")

    images_out_root = output_dir / "images"
    masks_out_root = output_dir / "masks"
    images_out_root.mkdir(parents=True, exist_ok=True)
    masks_out_root.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[ManifestRow] = []
    selected_frames = [frame_start + i for i in range(num_frames)]

    for in_cam, out_cam in zip(in_cams, out_cams):
        in_img_dir = images_in_root / in_cam
        in_msk_dir = masks_in_root / in_cam
        img_map = _index_numeric_frames(in_img_dir)
        msk_map = _index_numeric_frames(in_msk_dir)
        for output_frame, frame_idx in enumerate(selected_frames):
            if frame_idx not in img_map:
                _fail(f"missing image frame {frame_idx} in {in_img_dir}")
            if frame_idx not in msk_map:
                _fail(f"missing mask frame {frame_idx} in {in_msk_dir}")

            img_path = img_map[frame_idx]
            msk_path = msk_map[frame_idx]

            out_img_dir = images_out_root / out_cam
            out_msk_dir = masks_out_root / out_cam
            out_img_dir.mkdir(parents=True, exist_ok=True)
            out_msk_dir.mkdir(parents=True, exist_ok=True)

            out_img_path = out_img_dir / f"{output_frame:06d}.jpg"
            out_msk_path = out_msk_dir / f"{output_frame:06d}.png"

            with Image.open(img_path) as im:
                rgb = _resize_rgb(im.convert("RGB"), image_downscale)
                rgb.save(out_img_path, quality=95)
            with Image.open(msk_path) as im:
                mask = _resize_mask(im.convert("L"), image_downscale)
                mask.save(out_msk_path)

            manifest_rows.append(
                ManifestRow(
                    input_cam=in_cam,
                    output_cam=out_cam,
                    input_frame=int(frame_idx),
                    output_frame=int(output_frame),
                    input_image=str(img_path),
                    output_image=str(out_img_path),
                    input_mask=str(msk_path),
                    output_mask=str(out_msk_path),
                )
            )

    (output_dir / "adapt_scene.json").write_text(
        json.dumps(
            {
                "input_dir": str(input_dir),
                "output_dir": str(output_dir),
                "input_cameras": in_cams,
                "output_cameras": out_cams,
                "frame_start": frame_start,
                "num_frames": num_frames,
                "image_downscale": image_downscale,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with (output_dir / "adapt_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "input_cam",
                "output_cam",
                "input_frame",
                "output_frame",
                "input_image",
                "output_image",
                "input_mask",
                "output_mask",
            ]
        )
        for row in manifest_rows:
            writer.writerow(
                [
                    row.input_cam,
                    row.output_cam,
                    row.input_frame,
                    row.output_frame,
                    row.input_image,
                    row.output_image,
                    row.input_mask,
                    row.output_mask,
                ]
            )

    print(f"[THUman4Adapter] wrote: {output_dir}")
    print(f"[THUman4Adapter] cameras: {len(out_cams)} {out_cams}")
    print(f"[THUman4Adapter] frames: {num_frames} (start={frame_start})")
    print("[THUman4Adapter] NOTE: local-eval only; do NOT commit data/ outputs/")


if __name__ == "__main__":
    main()
