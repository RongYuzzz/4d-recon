#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def parse_camera_ids(images_dir: Path, camera_ids_arg: str | None) -> list[str]:
    all_cams = sorted([p.name for p in images_dir.iterdir() if p.is_dir()])
    if not all_cams:
        raise FileNotFoundError(f"No camera folders found under: {images_dir}")
    if not camera_ids_arg:
        return all_cams

    cams = [x.strip() for x in camera_ids_arg.split(",") if x.strip()]
    if not cams:
        raise ValueError("--camera_ids is empty")
    missing = [c for c in cams if c not in all_cams]
    if missing:
        raise ValueError(f"Camera folders not found: {missing}")
    return cams


def load_gray_image(cam_dir: Path, frame_idx: int) -> np.ndarray:
    for ext in (".jpg", ".png", ".jpeg"):
        p = cam_dir / f"{frame_idx:06d}{ext}"
        if p.exists():
            img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise RuntimeError(f"Failed to load image: {p}")
            return img
    raise FileNotFoundError(f"Frame image not found for {cam_dir.name} frame {frame_idx:06d}")


def draw_flow_overlay(gray0: np.ndarray, p0: np.ndarray, p1: np.ndarray, out_path: Path) -> None:
    canvas = cv2.cvtColor(gray0, cv2.COLOR_GRAY2BGR)
    step = max(1, len(p0) // 200)
    for a, b in zip(p0[::step], p1[::step]):
        x0, y0 = int(round(float(a[0]))), int(round(float(a[1])))
        x1, y1 = int(round(float(b[0]))), int(round(float(b[1])))
        cv2.arrowedLine(canvas, (x0, y0), (x1, y1), (0, 255, 255), 1, tipLength=0.2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(out_path), canvas)
    if not ok:
        raise RuntimeError(f"Failed to write viz image: {out_path}")


def run_extraction(
    data_dir: Path,
    camera_ids: list[str],
    frame_start: int,
    num_frames: int,
    max_tracks_per_pair: int,
    min_track_len: int,
    out_npz: Path,
    viz_dir: Path | None,
) -> int:
    if min_track_len != 1:
        raise ValueError("Current implementation only supports --min_track_len 1 (t -> t+1)")
    if num_frames < 2:
        raise ValueError("--num_frames must be >= 2 for temporal correspondences")

    images_dir = data_dir / "images"
    if not images_dir.exists():
        raise FileNotFoundError(f"Missing images dir: {images_dir}")

    first_cam_img = load_gray_image(images_dir / camera_ids[0], frame_start)
    image_height, image_width = int(first_cam_img.shape[0]), int(first_cam_img.shape[1])

    src_cam_idx_list: list[np.ndarray] = []
    src_frame_offset_list: list[np.ndarray] = []
    dst_frame_offset_list: list[np.ndarray] = []
    src_xy_list: list[np.ndarray] = []
    dst_xy_list: list[np.ndarray] = []
    weight_list: list[np.ndarray] = []

    total_pairs = 0
    for cam_idx, cam_name in enumerate(camera_ids):
        cam_dir = images_dir / cam_name
        wrote_viz_for_cam = False
        for fo in range(num_frames - 1):
            src_frame = frame_start + fo
            dst_frame = src_frame + 1

            gray0 = load_gray_image(cam_dir, src_frame)
            gray1 = load_gray_image(cam_dir, dst_frame)
            if gray0.shape != gray1.shape:
                raise ValueError(f"Shape mismatch for {cam_name}: {src_frame} vs {dst_frame}")

            p0 = cv2.goodFeaturesToTrack(
                gray0,
                maxCorners=max_tracks_per_pair * 2,
                qualityLevel=0.01,
                minDistance=4,
                blockSize=7,
            )
            if p0 is None or len(p0) == 0:
                continue

            p1, st, err = cv2.calcOpticalFlowPyrLK(
                gray0,
                gray1,
                p0,
                None,
                winSize=(21, 21),
                maxLevel=3,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
            )
            if p1 is None or st is None:
                continue

            p0v = p0.reshape(-1, 2)
            p1v = p1.reshape(-1, 2)
            stv = st.reshape(-1).astype(bool)
            errv = err.reshape(-1) if err is not None else np.zeros((p0v.shape[0],), dtype=np.float32)

            finite_mask = np.isfinite(p0v).all(axis=1) & np.isfinite(p1v).all(axis=1)
            in_bound_src = (
                (p0v[:, 0] >= 0)
                & (p0v[:, 0] < image_width)
                & (p0v[:, 1] >= 0)
                & (p0v[:, 1] < image_height)
            )
            in_bound_dst = (
                (p1v[:, 0] >= 0)
                & (p1v[:, 0] < image_width)
                & (p1v[:, 1] >= 0)
                & (p1v[:, 1] < image_height)
            )
            keep = stv & finite_mask & in_bound_src & in_bound_dst & np.isfinite(errv)

            if not np.any(keep):
                continue

            p0k = p0v[keep]
            p1k = p1v[keep]
            errk = errv[keep]

            if p0k.shape[0] > max_tracks_per_pair:
                sel = np.argsort(errk)[:max_tracks_per_pair]
                p0k = p0k[sel]
                p1k = p1k[sel]

            n = p0k.shape[0]
            if n == 0:
                continue

            src_cam_idx_list.append(np.full((n,), cam_idx, dtype=np.int16))
            src_frame_offset_list.append(np.full((n,), fo, dtype=np.int16))
            dst_frame_offset_list.append(np.full((n,), fo + 1, dtype=np.int16))
            src_xy_list.append(p0k.astype(np.float32))
            dst_xy_list.append(p1k.astype(np.float32))
            weight_list.append(np.ones((n,), dtype=np.float32))
            total_pairs += n

            if viz_dir is not None and not wrote_viz_for_cam:
                viz_name = f"frame{src_frame:06d}_to_{dst_frame:06d}_cam{cam_name}.jpg"
                draw_flow_overlay(gray0, p0k, p1k, viz_dir / viz_name)
                wrote_viz_for_cam = True

    if src_xy_list:
        src_cam_idx = np.concatenate(src_cam_idx_list, axis=0)
        src_frame_offset = np.concatenate(src_frame_offset_list, axis=0)
        dst_frame_offset = np.concatenate(dst_frame_offset_list, axis=0)
        src_xy = np.concatenate(src_xy_list, axis=0)
        dst_xy = np.concatenate(dst_xy_list, axis=0)
        weight = np.concatenate(weight_list, axis=0)
    else:
        src_cam_idx = np.zeros((0,), dtype=np.int16)
        src_frame_offset = np.zeros((0,), dtype=np.int16)
        dst_frame_offset = np.zeros((0,), dtype=np.int16)
        src_xy = np.zeros((0, 2), dtype=np.float32)
        dst_xy = np.zeros((0, 2), dtype=np.float32)
        weight = np.zeros((0,), dtype=np.float32)

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        camera_names=np.array(camera_ids),
        frame_start=np.int32(frame_start),
        num_frames=np.int32(num_frames),
        image_width=np.int32(image_width),
        image_height=np.int32(image_height),
        src_cam_idx=src_cam_idx,
        src_frame_offset=src_frame_offset,
        dst_frame_offset=dst_frame_offset,
        src_xy=src_xy,
        dst_xy=dst_xy,
        weight=weight,
    )
    return int(total_pairs)


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract temporal correspondences using KLT")
    ap.add_argument("--data_dir", required=True, help="Dataset root with images/ and sparse/")
    ap.add_argument("--camera_ids", default="", help="Comma-separated camera ids; default all")
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--num_frames", type=int, default=60)
    ap.add_argument("--max_tracks_per_pair", type=int, default=500)
    ap.add_argument("--min_track_len", type=int, default=1)
    ap.add_argument("--out_npz", required=True)
    ap.add_argument("--viz_dir", default="")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if args.frame_start < 0:
        raise ValueError("--frame_start must be >= 0")
    if args.num_frames <= 0:
        raise ValueError("--num_frames must be > 0")
    if args.max_tracks_per_pair <= 0:
        raise ValueError("--max_tracks_per_pair must be > 0")

    camera_ids = parse_camera_ids(data_dir / "images", args.camera_ids)
    viz_dir = Path(args.viz_dir) if args.viz_dir else None
    out_npz = Path(args.out_npz)

    total_pairs = run_extraction(
        data_dir=data_dir,
        camera_ids=camera_ids,
        frame_start=args.frame_start,
        num_frames=args.num_frames,
        max_tracks_per_pair=args.max_tracks_per_pair,
        min_track_len=args.min_track_len,
        out_npz=out_npz,
        viz_dir=viz_dir,
    )

    print(f"[Info] data_dir: {data_dir}")
    print(f"[Info] cameras: {','.join(camera_ids)}")
    print(f"[Info] frame_range: [{args.frame_start}, {args.frame_start + args.num_frames})")
    print(f"[Info] out_npz: {out_npz}")
    if viz_dir is not None:
        print(f"[Info] viz_dir: {viz_dir}")
    print(f"[Info] correspondences: {total_pairs}")


if __name__ == "__main__":
    main()
