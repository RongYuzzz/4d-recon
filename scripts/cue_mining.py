#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image


_FRAME_RE = re.compile(r"^(\d+)\.(jpg|jpeg|png)$", re.IGNORECASE)


def _fail(message: str) -> None:
    raise RuntimeError(message)


def _list_camera_names(images_dir: Path) -> list[str]:
    if not images_dir.is_dir():
        _fail(f"images directory not found: {images_dir}")
    names = sorted(p.name for p in images_dir.iterdir() if p.is_dir())
    if not names:
        _fail(f"no camera folders under: {images_dir}")
    return names


def _index_camera_frames(camera_dir: Path) -> dict[int, Path]:
    frame_map: dict[int, Path] = {}
    for child in camera_dir.iterdir():
        if not child.is_file():
            continue
        m = _FRAME_RE.match(child.name)
        if m:
            frame_map[int(m.group(1))] = child
    if not frame_map:
        _fail(f"no frame images found under: {camera_dir}")
    return frame_map


def _read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


def _to_gray(image_rgb: np.ndarray) -> np.ndarray:
    rgb = image_rgb.astype(np.float32)
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def _downsample_mask(mask: np.ndarray, downscale: int) -> np.ndarray:
    """Downsample a soft mask/weight map to uint8 [0,255]."""
    if downscale <= 1:
        if mask.dtype == np.uint8:
            return mask
        return np.clip(mask * 255.0, 0.0, 255.0).astype(np.uint8)
    h, w = mask.shape
    target_w = max(1, w // downscale)
    target_h = max(1, h // downscale)
    if mask.dtype == np.uint8:
        m_img = Image.fromarray(mask, mode="L")
    else:
        m_img = Image.fromarray(np.clip(mask * 255.0, 0.0, 255.0).astype(np.uint8), mode="L")
    # Use bilinear to preserve soft weights (acts like local averaging).
    m_small = m_img.resize((target_w, target_h), resample=Image.Resampling.BILINEAR)
    return np.asarray(m_small, dtype=np.uint8)


def _build_overlay(image_rgb: np.ndarray, mask_hw: np.ndarray) -> np.ndarray:
    overlay = image_rgb.astype(np.float32).copy()
    # mask in [0,1], used as tint strength.
    if mask_hw.dtype == np.uint8:
        mask = (mask_hw.astype(np.float32) / 255.0)[..., None]
    else:
        mask = np.clip(mask_hw.astype(np.float32), 0.0, 1.0)[..., None]
    tint = np.array([255.0, 40.0, 40.0], dtype=np.float32)[None, None, :]
    alpha = 0.45
    overlay = overlay * (1.0 - alpha * mask) + tint * (alpha * mask)
    return np.clip(overlay, 0.0, 255.0).astype(np.uint8)


def _upsample_mask(mask_small: np.ndarray, out_hw: tuple[int, int]) -> np.ndarray:
    h, w = out_hw
    if mask_small.dtype != np.uint8:
        mask_small = np.clip(mask_small * 255.0, 0.0, 255.0).astype(np.uint8)
    m_img = Image.fromarray(mask_small, mode="L")
    m_big = m_img.resize((w, h), resample=Image.Resampling.BILINEAR)
    return np.asarray(m_big, dtype=np.uint8)


def _save_grid(images: list[np.ndarray], out_path: Path, max_cols: int = 4) -> None:
    if not images:
        _fail("cannot build grid with empty images")
    h, w = images[0].shape[:2]
    for img in images:
        if img.shape[:2] != (h, w):
            _fail("grid images must have identical resolution")
    cols = min(max_cols, len(images))
    rows = int(math.ceil(len(images) / cols))
    canvas = Image.new("RGB", (cols * w, rows * h))
    for i, img in enumerate(images):
        r = i // cols
        c = i % cols
        canvas.paste(Image.fromarray(img), (c * w, r * h))
    canvas.save(out_path, quality=95)


def _masks_to_unit_float(masks: np.ndarray) -> np.ndarray:
    """Normalize masks to float32 in [0,1], compatible with {0,1} and {0,255}."""
    m = masks.astype(np.float32)
    if m.size == 0:
        return m
    if float(m.max()) > 1.0:
        m = m / 255.0
    return np.clip(m, 0.0, 1.0)


def _build_quality_stats(masks: np.ndarray) -> dict[str, object]:
    if masks.ndim != 4:
        _fail(f"quality stats expect masks shape [T,V,Hm,Wm], got {masks.shape}")

    m = _masks_to_unit_float(masks)
    mask_mean_per_t = [float(x) for x in m.mean(axis=(1, 2, 3))]
    mask_mean_per_view = [float(x) for x in m.mean(axis=(0, 2, 3))]
    mask_min = float(m.min()) if m.size else 0.0
    mask_max = float(m.max()) if m.size else 0.0
    temporal_flicker_l1_mean = (
        float(np.abs(m[1:] - m[:-1]).mean()) if m.shape[0] >= 2 else 0.0
    )
    all_black = bool(mask_max <= 1e-8)
    all_white = bool(mask_min >= 1.0 - 1e-8)

    return {
        "mask_mean_per_t": mask_mean_per_t,
        "mask_mean_per_view": mask_mean_per_view,
        "mask_min": mask_min,
        "mask_max": mask_max,
        "temporal_flicker_l1_mean": temporal_flicker_l1_mean,
        "all_black": all_black,
        "all_white": all_white,
    }


def _run_diff_backend(
    images_dir: Path,
    camera_names: list[str],
    frame_start: int,
    num_frames: int,
    mask_downscale: int,
    threshold_quantile: float,
) -> tuple[np.ndarray, dict[str, list[np.ndarray]]]:
    if not (0.0 < threshold_quantile < 1.0):
        _fail(f"threshold_quantile must be in (0,1), got {threshold_quantile}")
    if num_frames <= 0:
        _fail(f"num_frames must be > 0, got {num_frames}")
    if frame_start < 0:
        _fail(f"frame_start must be >= 0, got {frame_start}")
    if mask_downscale <= 0:
        _fail(f"mask_downscale must be >= 1, got {mask_downscale}")

    frame_cache: dict[str, list[np.ndarray]] = {}
    small_masks: list[list[np.ndarray]] = []
    frame_indices = [frame_start + i for i in range(num_frames)]

    for cam_name in camera_names:
        cam_dir = images_dir / cam_name
        frame_map = _index_camera_frames(cam_dir)
        missing = [idx for idx in frame_indices if idx not in frame_map]
        if missing:
            _fail(
                f"camera '{cam_name}' missing frames for requested range: "
                f"{missing[:5]}{'...' if len(missing) > 5 else ''}"
            )
        frames = [_read_rgb(frame_map[idx]) for idx in frame_indices]
        frame_cache[cam_name] = frames

        cam_masks: list[np.ndarray] = []
        for local_t in range(num_frames):
            curr = frames[local_t]
            prev = frames[max(local_t - 1, 0)]
            if curr.shape != prev.shape:
                _fail(f"inconsistent frame shape in camera '{cam_name}'")
            diff = np.abs(_to_gray(curr) - _to_gray(prev))
            thr = float(np.quantile(diff, threshold_quantile))
            diff_max = float(diff.max())
            if diff_max <= thr + 1e-6:
                dyn = np.zeros_like(diff, dtype=np.float32)
            else:
                # Soft dynamicness in [0,1]: 0 below threshold, 1 at max diff.
                dyn = np.clip((diff - thr) / (diff_max - thr + 1e-6), 0.0, 1.0).astype(np.float32)
            cam_masks.append(_downsample_mask(dyn, mask_downscale))
        small_masks.append(cam_masks)

    # Convert camera-major list into [T,V,Hm,Wm].
    masks_tv = []
    for t in range(num_frames):
        per_view = [small_masks[v][t] for v in range(len(camera_names))]
        hm, wm = per_view[0].shape
        for m in per_view:
            if m.shape != (hm, wm):
                _fail("all masks must have same Hm/Wm")
        masks_tv.append(np.stack(per_view, axis=0))
    masks = np.stack(masks_tv, axis=0).astype(np.uint8)  # [T,V,Hm,Wm]
    return masks, frame_cache


def _run_vggt_backend() -> None:
    _fail("internal: _run_vggt_backend called without args")


def _run_vggt_backend_impl(
    images_dir: Path,
    camera_names: list[str],
    frame_start: int,
    num_frames: int,
    mask_downscale: int,
    threshold_quantile: float,
    vggt_model_id: str,
    vggt_cache_dir: str,
    vggt_mode: str,
) -> tuple[np.ndarray, dict[str, list[np.ndarray]]]:
    if not (0.0 < threshold_quantile < 1.0):
        _fail(f"threshold_quantile must be in (0,1), got {threshold_quantile}")
    if num_frames <= 0:
        _fail(f"num_frames must be > 0, got {num_frames}")
    if frame_start < 0:
        _fail(f"frame_start must be >= 0, got {frame_start}")
    if mask_downscale <= 0:
        _fail(f"mask_downscale must be >= 1, got {mask_downscale}")
    if vggt_mode not in {"crop", "pad"}:
        _fail(f"vggt_mode must be 'crop' or 'pad', got {vggt_mode}")
    if not vggt_model_id.strip():
        _fail("vggt_model_id must be non-empty")

    try:
        import torch
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
    except Exception as exc:  # noqa: BLE001
        _fail(
            "backend=vggt requires VGGT package. "
            "Install with: pip install 'git+https://github.com/facebookresearch/vggt.git'. "
            f"import error: {exc}"
        )

    frame_indices = [frame_start + i for i in range(num_frames)]
    frame_maps: dict[str, dict[int, Path]] = {}
    frame_cache: dict[str, list[np.ndarray]] = {}
    for cam_name in camera_names:
        cam_dir = images_dir / cam_name
        frame_map = _index_camera_frames(cam_dir)
        missing = [idx for idx in frame_indices if idx not in frame_map]
        if missing:
            _fail(
                f"camera '{cam_name}' missing frames for requested range: "
                f"{missing[:5]}{'...' if len(missing) > 5 else ''}"
            )
        frame_maps[cam_name] = frame_map
        frame_cache[cam_name] = [_read_rgb(frame_map[frame_indices[0]])]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache_dir = vggt_cache_dir.strip() or None
    print(
        f"[CueMining][VGGT] loading model '{vggt_model_id}' "
        f"on device={device} cache_dir={cache_dir or '<default>'}"
    )
    try:
        model = VGGT.from_pretrained(vggt_model_id, cache_dir=cache_dir)
    except Exception as exc:  # noqa: BLE001
        _fail(
            "failed to load VGGT model from pretrained id "
            f"'{vggt_model_id}'. error: {exc}"
        )
    model = model.to(device).eval()

    masks_tv: list[np.ndarray] = []
    prev_depth: np.ndarray | None = None
    prev_conf: np.ndarray | None = None
    num_views = len(camera_names)
    eps = 1e-6

    for local_t, frame_idx in enumerate(frame_indices):
        image_paths = [str(frame_maps[cam_name][frame_idx]) for cam_name in camera_names]
        images = load_and_preprocess_images(image_paths, mode=vggt_mode).to(device)

        with torch.no_grad():
            if device == "cuda":
                with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
                    pred = model(images)
            else:
                pred = model(images)

        if "depth" not in pred:
            _fail("VGGT output missing key 'depth'")
        depth_t = pred["depth"].detach().float().cpu().numpy()
        if depth_t.ndim >= 4 and depth_t.shape[0] == 1:
            depth_t = depth_t[0]
        if depth_t.ndim >= 4 and depth_t.shape[-1] == 1:
            depth_t = depth_t[..., 0]
        if depth_t.ndim != 3:
            _fail(f"Unexpected VGGT depth shape: {depth_t.shape}")
        if depth_t.shape[0] != num_views:
            if depth_t.shape[-1] == num_views:
                depth_t = np.moveaxis(depth_t, -1, 0)
            else:
                _fail(f"VGGT depth view dim mismatch: shape={depth_t.shape}, expected V={num_views}")

        conf_t: np.ndarray | None = None
        if "depth_conf" in pred:
            conf_t = pred["depth_conf"].detach().float().cpu().numpy()
            if conf_t.ndim >= 4 and conf_t.shape[0] == 1:
                conf_t = conf_t[0]
            if conf_t.ndim != 3:
                _fail(f"Unexpected VGGT depth_conf shape: {conf_t.shape}")
            if conf_t.shape[0] != num_views:
                if conf_t.shape[-1] == num_views:
                    conf_t = np.moveaxis(conf_t, -1, 0)
                else:
                    _fail(
                        f"VGGT depth_conf view dim mismatch: shape={conf_t.shape}, expected V={num_views}"
                    )

        if prev_depth is None:
            dyn_views = [
                _downsample_mask(np.zeros_like(depth_t[v], dtype=np.float32), mask_downscale)
                for v in range(num_views)
            ]
        else:
            # Use temporal variation of log-depth as dynamic cue.
            diff = np.abs(
                np.log(np.clip(depth_t, eps, None)) - np.log(np.clip(prev_depth, eps, None))
            ).astype(np.float32)
            if conf_t is not None and prev_conf is not None:
                pair_conf = np.minimum(np.clip(conf_t, 0.0, 1.0), np.clip(prev_conf, 0.0, 1.0))
                diff *= pair_conf.astype(np.float32)

            dyn_views = []
            for v in range(num_views):
                dv = diff[v]
                thr = float(np.quantile(dv, threshold_quantile))
                dv_max = float(dv.max())
                if dv_max <= thr + 1e-6:
                    dyn = np.zeros_like(dv, dtype=np.float32)
                else:
                    dyn = np.clip((dv - thr) / (dv_max - thr + 1e-6), 0.0, 1.0).astype(np.float32)
                dyn_views.append(_downsample_mask(dyn, mask_downscale))

        masks_tv.append(np.stack(dyn_views, axis=0))
        prev_depth = depth_t
        prev_conf = conf_t

        if local_t == 0 or local_t == num_frames - 1 or (local_t + 1) % 10 == 0:
            print(f"[CueMining][VGGT] processed frame {local_t + 1}/{num_frames}")

        # Free temporary tensors early to reduce peak memory in long loops.
        del pred, images
        if device == "cuda":
            torch.cuda.empty_cache()

    masks = np.stack(masks_tv, axis=0).astype(np.uint8)  # [T,V,Hm,Wm]
    return masks, frame_cache


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Cue mining MVP for weak fusion masks")
    ap.add_argument("--data_dir", required=True, help="Dataset root containing images/<cam>/<frame>.jpg")
    ap.add_argument("--out_dir", required=True, help="Output directory under outputs/cue_mining/<tag>")
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--num_frames", type=int, default=60)
    ap.add_argument("--mask_downscale", type=int, default=4)
    ap.add_argument("--backend", choices=["diff", "vggt", "zeros"], default="diff")
    ap.add_argument("--threshold_quantile", type=float, default=0.9)
    ap.add_argument("--temporal_smoothing", choices=["none", "median3"], default="median3")
    ap.add_argument(
        "--vggt_model_id",
        default="facebook/VGGT-1B",
        help="Hugging Face model id for VGGT backend",
    )
    ap.add_argument(
        "--vggt_cache_dir",
        default="",
        help="Optional cache dir for VGGT weights (empty uses default HF cache)",
    )
    ap.add_argument(
        "--vggt_mode",
        choices=["crop", "pad"],
        default="crop",
        help="VGGT preprocess mode passed to load_and_preprocess_images",
    )
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    images_dir = data_dir / "images"
    camera_names = _list_camera_names(images_dir)

    if out_dir.exists() and not args.overwrite:
        _fail(f"out_dir already exists: {out_dir} (use --overwrite to replace)")
    out_dir.mkdir(parents=True, exist_ok=True)
    viz_dir = out_dir / "viz"
    viz_dir.mkdir(parents=True, exist_ok=True)

    if args.backend == "vggt":
        masks, _ = _run_vggt_backend_impl(
            images_dir=images_dir,
            camera_names=camera_names,
            frame_start=args.frame_start,
            num_frames=args.num_frames,
            mask_downscale=args.mask_downscale,
            threshold_quantile=args.threshold_quantile,
            vggt_model_id=args.vggt_model_id,
            vggt_cache_dir=args.vggt_cache_dir,
            vggt_mode=args.vggt_mode,
        )
    if args.backend == "zeros":
        if args.num_frames <= 0:
            _fail(f"num_frames must be > 0, got {args.num_frames}")
        if args.mask_downscale <= 0:
            _fail(f"mask_downscale must be >= 1, got {args.mask_downscale}")
        # Constant-zero dynamicness mask (no cue). Still satisfies contract and enables control runs.
        # Shape: [T,V,Hm,Wm]
        first_cam = camera_names[0]
        first_map = _index_camera_frames(images_dir / first_cam)
        if args.frame_start not in first_map:
            _fail(f"camera '{first_cam}' missing frame {args.frame_start} for backend=zeros")
        example = _read_rgb(first_map[args.frame_start])
        h, w = example.shape[:2]
        hm, wm = max(1, h // args.mask_downscale), max(1, w // args.mask_downscale)
        masks = np.zeros((args.num_frames, len(camera_names), hm, wm), dtype=np.uint8)
    elif args.backend == "diff":
        masks, _ = _run_diff_backend(
            images_dir=images_dir,
            camera_names=camera_names,
            frame_start=args.frame_start,
            num_frames=args.num_frames,
            mask_downscale=args.mask_downscale,
            threshold_quantile=args.threshold_quantile,
        )

    if args.temporal_smoothing == "median3" and masks.shape[0] >= 3:
        t, v, hm, wm = masks.shape
        smoothed = np.empty_like(masks)
        for ti in range(t):
            i0 = max(0, ti - 1)
            i1 = ti
            i2 = min(t - 1, ti + 1)
            window = np.stack([masks[i0], masks[i1], masks[i2]], axis=0)  # [3,V,Hm,Wm]
            smoothed[ti] = np.median(window, axis=0).astype(np.uint8)
        masks = smoothed

    npz_path = out_dir / "pseudo_masks.npz"
    np.savez_compressed(
        npz_path,
        masks=masks,
        camera_names=np.asarray(camera_names),
        frame_start=np.int32(args.frame_start),
        num_frames=np.int32(args.num_frames),
        mask_downscale=np.int32(args.mask_downscale),
    )
    quality = _build_quality_stats(masks)
    quality_path = out_dir / "quality.json"
    quality_path.write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")

    # Keep fixed viz names for report reuse and add per-cam overlays for quick sanity checks.
    frame_maps = {cam_name: _index_camera_frames(images_dir / cam_name) for cam_name in camera_names}
    overlay_local_indices = [0]
    if args.num_frames > 30:
        overlay_local_indices.append(30)

    for cam_i, cam_name in enumerate(camera_names):
        for local_t in overlay_local_indices:
            frame_idx = args.frame_start + local_t
            frame_path = frame_maps[cam_name].get(frame_idx)
            if frame_path is None:
                _fail(f"camera '{cam_name}' missing frame {frame_idx} for overlay output")
            rgb = _read_rgb(frame_path)
            m_big = _upsample_mask(masks[local_t, cam_i], rgb.shape[:2])
            overlay = _build_overlay(rgb, m_big)
            out_name = f"overlay_cam{cam_name}_frame{local_t:06d}.jpg"
            Image.fromarray(overlay).save(viz_dir / out_name, quality=95)

    # Backward-compatible alias for existing reports.
    overlay_cam = "02" if "02" in camera_names else camera_names[0]
    legacy_src = viz_dir / f"overlay_cam{overlay_cam}_frame000000.jpg"
    legacy_dst = viz_dir / "overlay_cam02_frame000000.jpg"
    if not legacy_src.exists():
        _fail(f"legacy overlay source missing: {legacy_src}")
    if legacy_src != legacy_dst:
        legacy_dst.write_bytes(legacy_src.read_bytes())

    grid_imgs = []
    for cam_i, cam_name in enumerate(camera_names):
        frame_path = frame_maps[cam_name].get(args.frame_start)
        if frame_path is None:
            _fail(f"camera '{cam_name}' missing frame {args.frame_start} for grid output")
        rgb = _read_rgb(frame_path)
        m_big = _upsample_mask(masks[0, cam_i], rgb.shape[:2])
        grid_imgs.append(_build_overlay(rgb, m_big))
    _save_grid(grid_imgs, viz_dir / "grid_frame000000.jpg", max_cols=4)

    print(f"[CueMining] backend: {args.backend}")
    print(f"[CueMining] temporal_smoothing: {args.temporal_smoothing}")
    print(f"[CueMining] data_dir: {data_dir}")
    print(f"[CueMining] out_dir: {out_dir}")
    print(f"[CueMining] cameras: {len(camera_names)} ({camera_names})")
    print(
        f"[CueMining] frames: [{args.frame_start}, {args.frame_start + args.num_frames}) "
        f"num_frames={args.num_frames}"
    )
    print(
        f"[CueMining] masks shape: {tuple(masks.shape)} dtype={masks.dtype} "
        f"range=[{int(masks.min())},{int(masks.max())}]"
    )
    print(f"[CueMining] npz: {npz_path}")
    print(
        "[CueMining] quality: "
        f"mean_t_avg={float(np.mean(quality['mask_mean_per_t'])):.6f} "
        f"mean_v_avg={float(np.mean(quality['mask_mean_per_view'])):.6f} "
        f"min={float(quality['mask_min']):.6f} max={float(quality['mask_max']):.6f} "
        f"flicker_l1={float(quality['temporal_flicker_l1_mean']):.6f} "
        f"all_black={bool(quality['all_black'])} all_white={bool(quality['all_white'])}"
    )
    print(f"[CueMining] quality_json: {quality_path}")
    print(f"[CueMining] viz: {viz_dir}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"[CueMining][ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
