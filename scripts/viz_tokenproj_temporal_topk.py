#!/usr/bin/env python3
"""Visualize token_proj temporal top-k correspondences from a VGGT cache.

This is a lightweight, "answerable in a defense" visualization:
- Token-level (H×W grid), not pixel-level optical flow.
- Same camera, consecutive frames (t -> t+1).
- Cosine similarity, greedy dst de-dup, visualize top-k matches.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def _parse_csv_ints(arg: str) -> list[int]:
    items = [x.strip() for x in str(arg).replace(" ", ",").split(",") if x.strip()]
    if not items:
        raise ValueError("empty frames list")
    out: list[int] = []
    for x in items:
        try:
            out.append(int(x))
        except ValueError as exc:  # noqa: PERF203
            raise ValueError(f"invalid int: {x}") from exc
    return out


def _parse_camera_ids(arg: str) -> list[str]:
    items = [x.strip() for x in str(arg).replace(" ", ",").split(",") if x.strip()]
    return [str(x) for x in items]


def _normalize_rows(x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    denom = np.linalg.norm(x, axis=1, keepdims=True)
    denom = np.maximum(denom, eps)
    return x / denom


def _sim_to_rgb(sim: float) -> tuple[int, int, int]:
    # Map cosine similarity [-1,1] to a red->yellow->green ramp.
    t = (float(sim) + 1.0) * 0.5
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.5:
        r = 255
        g = int(round(2.0 * t * 255.0))
        b = 0
    else:
        r = int(round(2.0 * (1.0 - t) * 255.0))
        g = 255
        b = 0
    return (int(np.clip(r, 0, 255)), int(np.clip(g, 0, 255)), int(np.clip(b, 0, 255)))


def _token_rc(idx: int, w: int) -> tuple[int, int]:
    r = idx // w
    c = idx % w
    return (int(r), int(c))


def _center_xy(origin_xy: tuple[int, int], cell: int, rc: tuple[int, int]) -> tuple[float, float]:
    ox, oy = origin_xy
    r, c = rc
    x = ox + (c + 0.5) * cell
    y = oy + (r + 0.5) * cell
    return (float(x), float(y))


def _draw_grid(draw: ImageDraw.ImageDraw, origin_xy: tuple[int, int], h: int, w: int, cell: int) -> None:
    ox, oy = origin_xy
    grid_w = w * cell
    grid_h = h * cell
    color = (220, 220, 220)
    for rr in range(h + 1):
        y = oy + rr * cell
        draw.line([(ox, y), (ox + grid_w, y)], fill=color, width=1)
    for cc in range(w + 1):
        x = ox + cc * cell
        draw.line([(x, oy), (x, oy + grid_h)], fill=color, width=1)


def _greedy_topk_matches(sim: np.ndarray, topk: int) -> list[tuple[int, int, float]]:
    # sim: (Nsrc, Ndst)
    if sim.ndim != 2:
        raise ValueError(f"sim must be 2D, got {sim.ndim}D")
    n_src, n_dst = [int(x) for x in sim.shape]
    if n_src <= 0 or n_dst <= 0:
        return []

    best_j = np.argmax(sim, axis=1).astype(int)
    best_s = sim[np.arange(n_src), best_j].astype(np.float32, copy=False)
    matches = [(int(i), int(best_j[i]), float(best_s[i])) for i in range(n_src)]
    matches.sort(key=lambda t: (t[2], -t[0], -t[1]), reverse=True)

    k = int(max(1, min(topk, n_src, n_dst)))
    used_dst: set[int] = set()
    kept: list[tuple[int, int, float]] = []
    for i, j, s in matches:
        if j in used_dst:
            continue
        kept.append((i, j, float(s)))
        used_dst.add(j)
        if len(kept) >= k:
            break
    return kept


def _viz_pair(
    phi_src_chw: np.ndarray,
    phi_dst_chw: np.ndarray,
    out_path: Path,
    *,
    title: str,
    topk: int,
    cell: int,
    gap: int,
    margin: int,
    header_h: int,
) -> None:
    if phi_src_chw.ndim != 3 or phi_dst_chw.ndim != 3:
        raise ValueError("phi_src/dst must be (C,H,W)")
    c, h, w = [int(x) for x in phi_src_chw.shape]
    c2, h2, w2 = [int(x) for x in phi_dst_chw.shape]
    if (c2, h2, w2) != (c, h, w):
        raise ValueError(f"phi src/dst shape mismatch: {(c,h,w)} vs {(c2,h2,w2)}")

    # Flatten tokens to (N,C).
    src = np.transpose(phi_src_chw, (1, 2, 0)).reshape(-1, c).astype(np.float32)
    dst = np.transpose(phi_dst_chw, (1, 2, 0)).reshape(-1, c).astype(np.float32)
    src = _normalize_rows(src)
    dst = _normalize_rows(dst)
    sim = src @ dst.T  # (N,N)

    matches = _greedy_topk_matches(sim, topk=int(topk))
    if not matches:
        raise ValueError("no matches produced (unexpected empty similarity matrix)")

    grid_w = w * cell
    grid_h = h * cell
    canvas_w = margin * 2 + grid_w * 2 + gap
    canvas_h = header_h + margin * 2 + grid_h
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    draw.text((margin, 8), title, fill=(0, 0, 0))

    left_origin = (margin, header_h + margin)
    right_origin = (margin + grid_w + gap, header_h + margin)
    _draw_grid(draw, left_origin, h=h, w=w, cell=cell)
    _draw_grid(draw, right_origin, h=h, w=w, cell=cell)

    # Draw lines first, then endpoints.
    for i, j, s in matches:
        src_rc = _token_rc(i, w=w)
        dst_rc = _token_rc(j, w=w)
        x0, y0 = _center_xy(left_origin, cell=cell, rc=src_rc)
        x1, y1 = _center_xy(right_origin, cell=cell, rc=dst_rc)
        color = _sim_to_rgb(float(s))
        draw.line([(x0, y0), (x1, y1)], fill=color, width=2)

    r = max(2, cell // 10)
    for i, j, s in matches:
        src_rc = _token_rc(i, w=w)
        dst_rc = _token_rc(j, w=w)
        x0, y0 = _center_xy(left_origin, cell=cell, rc=src_rc)
        x1, y1 = _center_xy(right_origin, cell=cell, rc=dst_rc)
        color = _sim_to_rgb(float(s))
        draw.ellipse([(x0 - r, y0 - r), (x0 + r, y0 + r)], outline=color, width=2)
        draw.ellipse([(x1 - r, y1 - r), (x1 + r, y1 + r)], outline=color, width=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, quality=95)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache_npz", required=True, help="Path to VGGT cache gt_cache.npz")
    ap.add_argument("--out_dir", required=True, help="Output directory for images (e.g., outputs/correspondences/.../viz)")
    ap.add_argument("--frames", default="0,30", help="Comma-separated src frame offsets within cache (t -> t+1).")
    ap.add_argument("--topk", type=int, default=20, help="Top-k correspondences to visualize (greedy dst de-dup).")
    ap.add_argument("--camera_ids", default="", help="Optional comma-separated subset of camera ids (e.g., 02,05).")
    ap.add_argument("--cell", type=int, default=48, help="Token grid cell size (pixels).")
    ap.add_argument("--gap", type=int, default=80, help="Horizontal gap between src/dst grids (pixels).")
    ap.add_argument("--margin", type=int, default=20, help="Canvas margin (pixels).")
    ap.add_argument("--header_h", type=int, default=40, help="Header height (pixels).")
    args = ap.parse_args()

    cache_npz = Path(args.cache_npz)
    out_dir = Path(args.out_dir)
    frames = _parse_csv_ints(args.frames)

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

    for fo in frames:
        if fo < 0 or fo >= t - 1:
            raise ValueError(f"frame offset out of range for t->t+1: {fo} (T={t})")

    cam_keep: list[int]
    if args.camera_ids:
        keep_names = _parse_camera_ids(args.camera_ids)
        missing = [x for x in keep_names if x not in camera_names]
        if missing:
            raise ValueError(f"camera_ids not found in cache: {missing}")
        cam_keep = [camera_names.index(x) for x in keep_names]
    else:
        cam_keep = list(range(v))

    out_dir.mkdir(parents=True, exist_ok=True)
    for cam_idx in cam_keep:
        cam = camera_names[cam_idx]
        for fo in frames:
            src_frame = frame_start + fo
            dst_frame = frame_start + fo + 1
            out_path = out_dir / f"token_top{int(args.topk)}_cam{cam}_frame{src_frame:06d}_to_{dst_frame:06d}.jpg"
            title = f"token_proj temporal top-{int(args.topk)} | cam{cam} | {src_frame:06d}->{dst_frame:06d}"
            _viz_pair(
                phi_src_chw=phi[fo, cam_idx],
                phi_dst_chw=phi[fo + 1, cam_idx],
                out_path=out_path,
                title=title,
                topk=int(args.topk),
                cell=int(args.cell),
                gap=int(args.gap),
                margin=int(args.margin),
                header_h=int(args.header_h),
            )
            print(f"[viz] wrote {out_path}")


if __name__ == "__main__":
    main()

