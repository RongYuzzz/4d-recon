#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def _parse_csv_ints(arg: str) -> list[int]:
    items = [x.strip() for x in arg.replace(" ", ",").split(",") if x.strip()]
    if not items:
        raise ValueError("empty list")
    out: list[int] = []
    for x in items:
        try:
            out.append(int(x))
        except ValueError as exc:  # noqa: PERF203
            raise ValueError(f"invalid int: {x}") from exc
    return out


def _fix_component_sign(components: np.ndarray) -> np.ndarray:
    # PCA directions have sign ambiguity. Make sign deterministic by forcing the
    # largest-magnitude loading in each component to be positive.
    comps = components.copy()
    for k in range(comps.shape[0]):
        idx = int(np.argmax(np.abs(comps[k])))
        if float(comps[k, idx]) < 0.0:
            comps[k] *= -1.0
    return comps


def pca_rgb_for_frame(phi_vchw: np.ndarray) -> np.ndarray:
    if phi_vchw.ndim != 4:
        raise ValueError(f"phi_vchw must be 4D (V,C,H,W), got {phi_vchw.ndim}D")
    v, c, h, w = [int(x) for x in phi_vchw.shape]
    if c < 3:
        raise ValueError(f"C must be >= 3 for PCA->RGB, got {c}")

    x = np.transpose(phi_vchw, (0, 2, 3, 1)).reshape(-1, c).astype(np.float32)
    x = x - x.mean(axis=0, keepdims=True)

    # SVD is stable and fast here (N=V*H*W <= 8*9*9=648 for our cache).
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    comps = vt[:3].astype(np.float32, copy=False)
    comps = _fix_component_sign(comps)

    proj = x @ comps.T  # (N,3)
    lo = np.percentile(proj, 1.0, axis=0)
    hi = np.percentile(proj, 99.0, axis=0)
    denom = np.maximum(hi - lo, 1e-6)
    scaled = (proj - lo) / denom
    scaled = np.clip(scaled, 0.0, 1.0)
    rgb = np.round(scaled * 255.0).astype(np.uint8)
    return rgb.reshape(v, h, w, 3)


def _resize_nearest(img: np.ndarray, out_hw: tuple[int, int]) -> Image.Image:
    h, w = out_hw
    pil = Image.fromarray(img, mode="RGB")
    return pil.resize((w, h), resample=Image.NEAREST)


def _write_grid(
    tiles: list[Image.Image],
    labels: list[str],
    cols: int,
    out_path: Path,
) -> None:
    if len(tiles) != len(labels):
        raise ValueError("tiles/labels length mismatch")
    if not tiles:
        raise ValueError("empty tiles")
    if cols <= 0:
        raise ValueError("cols must be > 0")

    tile_w, tile_h = tiles[0].size
    rows = int(math.ceil(len(tiles) / cols))
    canvas = Image.new("RGB", (cols * tile_w, rows * tile_h), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    for i, (tile, label) in enumerate(zip(tiles, labels, strict=True)):
        x = (i % cols) * tile_w
        y = (i // cols) * tile_h
        canvas.paste(tile, (x, y))
        # Simple legible label (top-left), no external font dependency.
        draw.text((x + 6, y + 6), str(label), fill=(255, 255, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, quality=95)


def main() -> None:
    ap = argparse.ArgumentParser(description="Visualize VGGT cache token_proj via per-frame PCA->RGB")
    ap.add_argument("--cache_npz", required=True, help="Path to gt_cache.npz")
    ap.add_argument("--out_dir", required=True, help="Output directory (e.g., outputs/vggt_cache/.../viz_pca)")
    ap.add_argument(
        "--frames",
        default="0",
        help="Comma-separated frame offsets within cache (e.g., 0,15,30).",
    )
    ap.add_argument(
        "--grid_cols",
        type=int,
        default=4,
        help="Number of columns in grid output.",
    )
    ap.add_argument(
        "--camera_ids",
        default="",
        help="Optional comma-separated subset of camera ids (e.g., 02,03). Default: all.",
    )
    args = ap.parse_args()

    cache_npz = Path(args.cache_npz)
    out_dir = Path(args.out_dir)

    obj = np.load(cache_npz, allow_pickle=True)
    if "phi" not in obj.files:
        raise ValueError("cache missing key: phi")
    if "camera_names" not in obj.files:
        raise ValueError("cache missing key: camera_names")

    phi = obj["phi"]
    if phi.ndim != 5:
        raise ValueError(f"phi must be 5D (T,V,C,H,W), got {phi.ndim}D")
    t, v, c, h, w = [int(x) for x in phi.shape]

    camera_names = [str(x) for x in obj["camera_names"].tolist()]
    if len(camera_names) != v:
        raise ValueError(f"camera_names length mismatch: {len(camera_names)} vs V={v}")

    frame_start = int(obj["frame_start"]) if "frame_start" in obj.files else 0

    if "input_size" in obj.files:
        input_size = np.asarray(obj["input_size"]).astype(int).tolist()
        if len(input_size) != 2:
            raise ValueError(f"input_size must be length=2, got {input_size}")
        out_hw = (int(input_size[0]), int(input_size[1]))
    else:
        out_hw = (h, w)

    frames = _parse_csv_ints(str(args.frames))
    for fo in frames:
        if fo < 0 or fo >= t:
            raise ValueError(f"frame offset out of range: {fo} (T={t})")

    cam_keep: list[int]
    if args.camera_ids:
        keep_names = [x.strip() for x in args.camera_ids.split(",") if x.strip()]
        missing = [x for x in keep_names if x not in camera_names]
        if missing:
            raise ValueError(f"camera_ids not found in cache: {missing}")
        cam_keep = [camera_names.index(x) for x in keep_names]
    else:
        cam_keep = list(range(v))

    out_dir.mkdir(parents=True, exist_ok=True)
    for fo in frames:
        rgb_vhw = pca_rgb_for_frame(phi[fo, cam_keep])
        global_frame = frame_start + fo

        tiles: list[Image.Image] = []
        labels: list[str] = []
        for local_i, cam_idx in enumerate(cam_keep):
            cam = camera_names[cam_idx]
            tile = _resize_nearest(rgb_vhw[local_i], out_hw=out_hw)
            out_path = out_dir / f"pca_rgb_cam{cam}_frame{global_frame:06d}.jpg"
            tile.save(out_path, quality=95)
            tiles.append(tile)
            labels.append(f"cam{cam}")

        grid_path = out_dir / f"grid_pca_frame{global_frame:06d}.jpg"
        _write_grid(tiles=tiles, labels=labels, cols=int(args.grid_cols), out_path=grid_path)

        print(f"[PCA] frame={global_frame:06d} wrote {len(tiles)} tiles + grid: {grid_path}")


if __name__ == "__main__":
    main()
