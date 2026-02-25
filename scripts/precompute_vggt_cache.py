#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def _parse_camera_ids(raw: str) -> list[str]:
    cams = [x.strip() for x in raw.split(",") if x.strip()]
    if not cams:
        _fail("--camera_ids must contain at least one camera id, e.g. 02,03")
    return cams


def _index_camera_frames(cam_dir: Path) -> dict[int, Path]:
    if not cam_dir.is_dir():
        _fail(f"camera dir not found: {cam_dir}")
    frame_map: dict[int, Path] = {}
    for p in sorted(cam_dir.glob("*.jpg")):
        m = re.match(r"^(\d+)$", p.stem)
        if m is None:
            continue
        idx = int(m.group(1))
        frame_map[idx] = p
    if not frame_map:
        _fail(f"no numeric jpg frames found in {cam_dir}")
    return frame_map


def _read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def _downscale_vchw(x: np.ndarray, downscale: int) -> np.ndarray:
    if downscale <= 1:
        return x.astype(np.float32, copy=False)
    if x.ndim != 4:
        _fail(f"expected VCHW tensor, got shape={x.shape}")
    h, w = int(x.shape[-2]), int(x.shape[-1])
    out_h = max(1, h // downscale)
    out_w = max(1, w // downscale)
    t = torch.from_numpy(x.astype(np.float32, copy=False))
    t = F.interpolate(t, size=(out_h, out_w), mode="bilinear", align_corners=False)
    return t.cpu().numpy().astype(np.float32, copy=False)


def _project_patch_tokens(tokens_snd: np.ndarray, proj_dim: int, proj_seed: int) -> np.ndarray:
    """
    Fixed random projection for patch tokens.

    Args:
        tokens_snd: [S,N,D] float-like tokens.
        proj_dim: output channel dimension.
        proj_seed: deterministic seed for projection matrix.
    Returns:
        projected tokens [S,N,proj_dim], float32.
    """
    tokens = np.asarray(tokens_snd, dtype=np.float32)
    if tokens.ndim != 3:
        _fail(f"tokens_snd must be [S,N,D], got shape={tokens.shape}")
    if proj_dim <= 0:
        _fail(f"proj_dim must be >0, got {proj_dim}")
    d_token = int(tokens.shape[-1])
    if d_token <= 0:
        _fail(f"token dim must be >0, got {d_token}")

    rng = np.random.default_rng(int(proj_seed))
    w = rng.standard_normal((int(proj_dim), d_token), dtype=np.float32)
    w = w / np.clip(np.linalg.norm(w, axis=1, keepdims=True), 1e-6, None)
    out = np.einsum("pd,snd->snp", w, tokens, optimize=True)
    return out.astype(np.float32, copy=False)


def _aggregator_tokens_to_snd(tokens: torch.Tensor, num_views: int, key: str) -> torch.Tensor:
    """Normalize aggregator output tokens into [S,N,D] where S=num_views."""
    x = tokens
    if not isinstance(x, torch.Tensor):
        _fail(f"VGGT aggregator '{key}' must be tensor, got {type(x)}")
    while x.ndim >= 4 and x.shape[0] == 1:
        x = x[0]
    if x.ndim != 3:
        _fail(f"unsupported aggregator token shape for '{key}': {tuple(x.shape)}")
    if x.shape[0] == num_views:
        return x.contiguous()
    if x.shape[1] == num_views:
        return x.permute(1, 0, 2).contiguous()
    _fail(f"cannot align aggregator tokens for '{key}', shape={tuple(x.shape)} num_views={num_views}")
    return x


def _infer_patch_hw(num_patch_tokens: int, input_h: int, input_w: int) -> tuple[int, int]:
    """Infer patch-grid size from token count and preprocess input shape."""
    if num_patch_tokens <= 0:
        _fail(f"num_patch_tokens must be >0, got {num_patch_tokens}")
    h_est = max(1, int(round(float(input_h) / 14.0)))
    w_est = max(1, int(round(float(input_w) / 14.0)))
    if h_est * w_est == num_patch_tokens:
        return h_est, w_est
    side = int(round(math.sqrt(float(num_patch_tokens))))
    if side * side == num_patch_tokens:
        return side, side
    h = max(1, int(math.floor(math.sqrt(float(num_patch_tokens)))))
    while h > 1 and (num_patch_tokens % h) != 0:
        h -= 1
    w = num_patch_tokens // h
    if h * w != num_patch_tokens:
        _fail(f"cannot infer patch HxW from N={num_patch_tokens}")
    return h, w


def _framediff_top_p_mask(diff_v1hw: np.ndarray, top_p: float) -> np.ndarray:
    """Build per-view top-p binary mask from diff map [V,1,H,W]."""
    diff = np.asarray(diff_v1hw, dtype=np.float32)
    if diff.ndim != 4 or diff.shape[1] != 1:
        _fail(f"diff map must be [V,1,H,W], got shape={diff.shape}")
    v, _, h, w = diff.shape
    total = int(h * w)
    if top_p <= 0.0:
        return np.zeros_like(diff, dtype=np.float32)
    if top_p >= 1.0:
        return np.ones_like(diff, dtype=np.float32)
    k = max(1, min(total, int(math.ceil(float(top_p) * float(total)))))
    flat = diff.reshape(v, total)
    mask_flat = np.zeros_like(flat, dtype=np.float32)
    for vi in range(v):
        idx = np.argpartition(flat[vi], -k)[-k:]
        mask_flat[vi, idx] = 1.0
    return mask_flat.reshape(v, 1, h, w)


def _to_vchw(pred: Any, num_views: int, key: str) -> np.ndarray:
    if not isinstance(pred, torch.Tensor):
        _fail(f"VGGT output '{key}' must be a torch.Tensor, got {type(pred)}")
    arr = pred.detach().float().cpu().numpy()

    while arr.ndim >= 5 and arr.shape[0] == 1:
        arr = arr[0]

    if arr.ndim == 3:
        if arr.shape[0] == num_views:
            return arr[:, None, :, :].astype(np.float32, copy=False)
        if arr.shape[-1] == num_views:
            arr = np.moveaxis(arr, -1, 0)
            return arr[:, None, :, :].astype(np.float32, copy=False)

    if arr.ndim == 4:
        if arr.shape[0] == num_views and arr.shape[1] <= 16:
            return arr.astype(np.float32, copy=False)  # V,C,H,W
        if arr.shape[0] == num_views and arr.shape[-1] <= 16:
            return np.moveaxis(arr, -1, 1).astype(np.float32, copy=False)  # V,H,W,C
        if arr.shape[1] == num_views and arr.shape[0] <= 16:
            return np.moveaxis(arr, 0, 1).astype(np.float32, copy=False)  # C,V,H,W
        if arr.shape[2] == num_views and arr.shape[-1] <= 16:
            arr = np.moveaxis(arr, 2, 0)  # H,W,V,C -> V,H,W,C
            return np.moveaxis(arr, -1, 1).astype(np.float32, copy=False)

    _fail(f"unsupported VGGT output shape for '{key}': {arr.shape}, expected view-major feature map")
    return np.empty((0,), dtype=np.float32)


def _compute_dummy_phi(
    frame_paths_by_cam: list[Path], downscale: int
) -> tuple[np.ndarray, list[int], list[int]]:
    cams_phi: list[np.ndarray] = []
    input_size: list[int] | None = None
    phi_size: list[int] | None = None

    for path in frame_paths_by_cam:
        rgb = _read_rgb(path)  # H,W,3 in [0,1]
        h, w = int(rgb.shape[0]), int(rgb.shape[1])
        if input_size is None:
            input_size = [h, w]
        chw = np.transpose(rgb, (2, 0, 1))[None, ...]  # 1,3,H,W
        chw = _downscale_vchw(chw, downscale)[0]  # 3,Hf,Wf
        if phi_size is None:
            phi_size = [int(chw.shape[1]), int(chw.shape[2])]
        cams_phi.append(chw)

    if input_size is None or phi_size is None:
        _fail("dummy backend produced empty features")
    return np.stack(cams_phi, axis=0), input_size, phi_size  # V,C,Hf,Wf


def _run_backend_dummy(
    frame_maps: dict[str, dict[int, Path]],
    camera_names: list[str],
    frame_indices: list[int],
    phi_downscale: int,
) -> tuple[np.ndarray, np.ndarray | None, list[int], list[int], dict[str, Any]]:
    phi_frames: list[np.ndarray] = []
    input_size: list[int] | None = None
    phi_size: list[int] | None = None

    for frame_idx in frame_indices:
        frame_paths = [frame_maps[cam][frame_idx] for cam in camera_names]
        phi_vchw, in_sz, out_sz = _compute_dummy_phi(frame_paths, phi_downscale)
        if input_size is None:
            input_size = in_sz
        if phi_size is None:
            phi_size = out_sz
        phi_frames.append(phi_vchw.astype(np.float32, copy=False))

    if input_size is None or phi_size is None:
        _fail("no frames generated for dummy backend")
    phi = np.stack(phi_frames, axis=0).astype(np.float32, copy=False)  # T,V,C,Hf,Wf
    return phi, None, input_size, phi_size, {}


def _run_backend_vggt(
    frame_maps: dict[str, dict[int, Path]],
    camera_names: list[str],
    frame_indices: list[int],
    phi_name: str,
    token_layer_idx: int,
    token_proj_dim: int,
    token_proj_seed: int,
    token_proj_normalize: bool,
    save_framediff_gate: bool,
    framediff_top_p: float,
    vggt_model_id: str,
    vggt_cache_dir: str,
    vggt_mode: str,
    phi_downscale: int,
) -> tuple[np.ndarray, np.ndarray | None, list[int], list[int], dict[str, Any]]:
    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
    except Exception as exc:  # noqa: BLE001
        _fail(
            "backend=vggt requires VGGT package. "
            "Install with: pip install 'git+https://github.com/facebookresearch/vggt.git'. "
            f"import error: {exc}"
        )

    if phi_name not in {"depth", "world_points", "token_proj"}:
        _fail(f"--phi_name for backend=vggt must be one of depth|world_points|token_proj, got {phi_name}")
    if vggt_mode not in {"crop", "pad"}:
        _fail(f"--vggt_mode must be crop|pad, got {vggt_mode}")
    if not vggt_model_id.strip():
        _fail("--vggt_model_id must be non-empty")
    if framediff_top_p < 0.0 or framediff_top_p > 1.0:
        _fail(f"--framediff_top_p must be in [0,1], got {framediff_top_p}")
    if phi_name == "token_proj" and token_proj_dim <= 0:
        _fail(f"--token_proj_dim must be >0 when phi_name=token_proj, got {token_proj_dim}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache_dir = vggt_cache_dir.strip() or None
    print(
        f"[VGGTCache] loading model '{vggt_model_id}' on device={device} "
        f"cache_dir={cache_dir or '<default>'}"
    )
    model = VGGT.from_pretrained(vggt_model_id, cache_dir=cache_dir).to(device).eval()
    for p in model.parameters():
        p.requires_grad_(False)

    phi_frames: list[np.ndarray] = []
    conf_frames: list[np.ndarray] = []
    gate_frames: list[np.ndarray] = []
    input_size: list[int] | None = None
    phi_size: list[int] | None = None
    num_views = len(camera_names)
    prev_gray_v1hw: np.ndarray | None = None

    for i, frame_idx in enumerate(frame_indices):
        image_paths = [str(frame_maps[cam][frame_idx]) for cam in camera_names]
        images = load_and_preprocess_images(image_paths, mode=vggt_mode).to(device)
        if images.ndim == 4:
            images_1xS = images[None, ...]
        elif images.ndim == 5:
            images_1xS = images
        else:
            _fail(f"unexpected preprocessed image tensor shape: {tuple(images.shape)}")
        images_s3hw = images_1xS[0]
        if input_size is None:
            input_size = [int(images_s3hw.shape[-2]), int(images_s3hw.shape[-1])]

        if phi_name == "token_proj":
            with torch.no_grad():
                if device == "cuda":
                    with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
                        agg_out = model.aggregator(images_1xS)
                else:
                    agg_out = model.aggregator(images_1xS)

            if not isinstance(agg_out, (tuple, list)) or len(agg_out) < 2:
                _fail("VGGT aggregator output must be (aggregated_tokens_list, patch_start_idx)")
            aggregated_tokens_list = agg_out[0]
            patch_start_idx = int(agg_out[1])
            if isinstance(aggregated_tokens_list, torch.Tensor):
                layer_tokens = aggregated_tokens_list
            else:
                if not isinstance(aggregated_tokens_list, (tuple, list)) or not aggregated_tokens_list:
                    _fail("VGGT aggregator returned empty aggregated_tokens_list")
                layer_idx = int(token_layer_idx)
                if layer_idx < 0:
                    layer_idx += len(aggregated_tokens_list)
                if layer_idx < 0 or layer_idx >= len(aggregated_tokens_list):
                    _fail(
                        "token_layer_idx out of range: "
                        f"{token_layer_idx} for {len(aggregated_tokens_list)} layers"
                    )
                layer_tokens = aggregated_tokens_list[layer_idx]

            tokens_snd = _aggregator_tokens_to_snd(layer_tokens, num_views=num_views, key="aggregator_tokens")
            if patch_start_idx < 0 or patch_start_idx >= int(tokens_snd.shape[1]):
                _fail(
                    f"invalid patch_start_idx={patch_start_idx} for token shape={tuple(tokens_snd.shape)}"
                )
            patch_tokens = tokens_snd[:, patch_start_idx:, :].contiguous()
            n_patch = int(patch_tokens.shape[1])
            patch_h, patch_w = _infer_patch_hw(n_patch, input_h=input_size[0], input_w=input_size[1])
            if patch_h * patch_w != n_patch:
                _fail(f"patch grid mismatch: HxW={patch_h}x{patch_w}, N={n_patch}")

            patch_np = patch_tokens.detach().float().cpu().numpy().astype(np.float32, copy=False)
            proj = _project_patch_tokens(
                patch_np,
                proj_dim=int(token_proj_dim),
                proj_seed=int(token_proj_seed),
            )  # [S,Npatch,proj_dim]
            phi_vchw = (
                proj.reshape(num_views, patch_h, patch_w, int(token_proj_dim))
                .transpose(0, 3, 1, 2)
                .astype(np.float32, copy=False)
            )
            phi_vchw = _downscale_vchw(phi_vchw, phi_downscale)
            if token_proj_normalize:
                norm = np.linalg.norm(phi_vchw, axis=1, keepdims=True)
                phi_vchw = phi_vchw / np.clip(norm, 1e-6, None)
        else:
            with torch.no_grad():
                if device == "cuda":
                    with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
                        pred = model(images_1xS)
                else:
                    pred = model(images_1xS)

            if phi_name not in pred:
                _fail(f"VGGT output missing key '{phi_name}'")
            phi_vchw = _to_vchw(pred[phi_name], num_views=num_views, key=phi_name)
            phi_vchw = _downscale_vchw(phi_vchw, phi_downscale)

            if phi_name == "depth" and "depth_conf" in pred:
                conf_vchw = _to_vchw(pred["depth_conf"], num_views=num_views, key="depth_conf")
                conf_vchw = _downscale_vchw(conf_vchw, phi_downscale)
                conf_frames.append(np.clip(conf_vchw, 0.0, 1.0).astype(np.float32, copy=False))

        if phi_size is None:
            phi_size = [int(phi_vchw.shape[-2]), int(phi_vchw.shape[-1])]
        phi_frames.append(phi_vchw.astype(np.float32, copy=False))

        if save_framediff_gate:
            gray = images_s3hw.float().mean(dim=1, keepdim=True)
            gray = F.interpolate(
                gray,
                size=(int(phi_vchw.shape[-2]), int(phi_vchw.shape[-1])),
                mode="bilinear",
                align_corners=False,
            )
            gray_np = gray.detach().cpu().numpy().astype(np.float32, copy=False)
            if prev_gray_v1hw is None:
                gate = np.zeros_like(gray_np, dtype=np.float32)
            else:
                diff = np.abs(gray_np - prev_gray_v1hw).astype(np.float32, copy=False)
                diff_t = torch.from_numpy(diff)
                diff_t = F.avg_pool2d(diff_t, kernel_size=3, stride=1, padding=1)
                gate = _framediff_top_p_mask(
                    diff_t.cpu().numpy().astype(np.float32, copy=False),
                    top_p=float(framediff_top_p),
                )
            gate_frames.append(gate.astype(np.float32, copy=False))
            prev_gray_v1hw = gray_np

        if i == 0 or i == len(frame_indices) - 1 or (i + 1) % 10 == 0:
            print(f"[VGGTCache] processed frame {i + 1}/{len(frame_indices)}")

        del images, images_1xS, images_s3hw
        if device == "cuda":
            torch.cuda.empty_cache()

    if input_size is None or phi_size is None:
        _fail("no frames generated for vggt backend")

    phi = np.stack(phi_frames, axis=0).astype(np.float32, copy=False)
    conf = None
    if conf_frames:
        conf = np.stack(conf_frames, axis=0).astype(np.float32, copy=False)
    extras: dict[str, Any] = {}
    if save_framediff_gate and gate_frames:
        extras["gate_framediff"] = np.stack(gate_frames, axis=0).astype(np.float32, copy=False)
        extras["framediff_top_p"] = float(framediff_top_p)
    if phi_name == "token_proj":
        extras["token_layer_idx"] = int(token_layer_idx)
        extras["token_proj_dim"] = int(token_proj_dim)
        extras["token_proj_seed"] = int(token_proj_seed)
        extras["phi_is_normalized"] = bool(token_proj_normalize)
    return phi, conf, input_size, phi_size, extras


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Precompute GT VGGT feature cache for feature-metric loss training"
    )
    ap.add_argument("--data_dir", required=True, help="Dataset root containing images/<cam>/<frame>.jpg")
    ap.add_argument("--out_dir", required=True, help="Output directory for gt_cache.npz and meta.json")
    ap.add_argument("--camera_ids", required=True, help="Comma-separated camera ids, e.g. 02,03,04")
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--num_frames", type=int, default=60)
    ap.add_argument("--backend", choices=["dummy", "vggt"], default="dummy")
    ap.add_argument(
        "--phi_name",
        default="depth",
        help="dummy backend uses dummy_rgb; vggt backend uses depth|world_points|token_proj",
    )
    ap.add_argument("--phi_downscale", type=int, default=4, help="Downscale factor in phi-space")
    ap.add_argument("--token_layer_idx", type=int, default=23, help="VGGT token layer index for token_proj")
    ap.add_argument("--token_proj_dim", type=int, default=32, help="Output channel dim for token_proj")
    ap.add_argument("--token_proj_seed", type=int, default=20260225, help="Random seed for token projection")
    ap.add_argument(
        "--token_proj_normalize",
        type=int,
        choices=[0, 1],
        default=1,
        help="Whether to channel-normalize projected token features before save",
    )
    ap.add_argument(
        "--save_framediff_gate",
        type=int,
        choices=[0, 1],
        default=1,
        help="Whether to save gate_framediff top-p mask into cache",
    )
    ap.add_argument("--framediff_top_p", type=float, default=0.10, help="Top-p ratio for framediff gate")
    ap.add_argument("--vggt_model_id", default="facebook/VGGT-1B")
    ap.add_argument("--vggt_cache_dir", default="")
    ap.add_argument("--vggt_mode", choices=["crop", "pad"], default="crop")
    ap.add_argument("--dtype", choices=["float16", "float32"], default="float16")
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    if args.frame_start < 0:
        _fail("--frame_start must be >= 0")
    if args.num_frames <= 0:
        _fail("--num_frames must be > 0")
    if args.phi_downscale <= 0:
        _fail("--phi_downscale must be >= 1")
    if args.framediff_top_p < 0.0 or args.framediff_top_p > 1.0:
        _fail("--framediff_top_p must be in [0,1]")
    if args.backend == "dummy" and args.phi_name != "dummy_rgb":
        _fail("--phi_name for backend=dummy must be 'dummy_rgb'")

    data_dir = Path(args.data_dir).resolve()
    images_dir = data_dir / "images"
    if not images_dir.is_dir():
        _fail(f"missing images dir: {images_dir}")
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    npz_path = out_dir / "gt_cache.npz"
    meta_path = out_dir / "meta.json"
    if (npz_path.exists() or meta_path.exists()) and not args.overwrite:
        _fail(
            f"output exists in {out_dir}; pass --overwrite to replace "
            f"({npz_path.name}, {meta_path.name})"
        )

    camera_names = _parse_camera_ids(args.camera_ids)
    frame_indices = [args.frame_start + i for i in range(args.num_frames)]

    frame_maps: dict[str, dict[int, Path]] = {}
    for cam_name in camera_names:
        frame_map = _index_camera_frames(images_dir / cam_name)
        missing = [idx for idx in frame_indices if idx not in frame_map]
        if missing:
            _fail(
                f"camera '{cam_name}' missing frames for requested range: "
                f"{missing[:5]}{'...' if len(missing) > 5 else ''}"
            )
        frame_maps[cam_name] = frame_map

    extras: dict[str, Any] = {}
    if args.backend == "dummy":
        phi, conf, input_size, phi_size, extras = _run_backend_dummy(
            frame_maps=frame_maps,
            camera_names=camera_names,
            frame_indices=frame_indices,
            phi_downscale=args.phi_downscale,
        )
    else:
        phi, conf, input_size, phi_size, extras = _run_backend_vggt(
            frame_maps=frame_maps,
            camera_names=camera_names,
            frame_indices=frame_indices,
            phi_name=args.phi_name,
            token_layer_idx=args.token_layer_idx,
            token_proj_dim=args.token_proj_dim,
            token_proj_seed=args.token_proj_seed,
            token_proj_normalize=bool(args.token_proj_normalize),
            save_framediff_gate=bool(args.save_framediff_gate),
            framediff_top_p=args.framediff_top_p,
            vggt_model_id=args.vggt_model_id,
            vggt_cache_dir=args.vggt_cache_dir,
            vggt_mode=args.vggt_mode,
            phi_downscale=args.phi_downscale,
        )

    target_dtype = np.float16 if args.dtype == "float16" else np.float32
    phi = phi.astype(target_dtype, copy=False)

    save_obj: dict[str, Any] = {
        "phi": phi,  # [T,V,C,Hf,Wf]
        "camera_names": np.asarray(camera_names),
        "frame_start": np.int64(args.frame_start),
        "num_frames": np.int64(args.num_frames),
        "phi_name": np.asarray(args.phi_name),
        "vggt_mode": np.asarray(args.vggt_mode),
        "input_size": np.asarray(input_size, dtype=np.int64),
        "phi_size": np.asarray(phi_size, dtype=np.int64),
    }
    if conf is not None:
        save_obj["conf"] = conf.astype(target_dtype, copy=False)
    gate_framediff = extras.get("gate_framediff")
    if gate_framediff is not None:
        gate = np.asarray(gate_framediff)
        if gate.ndim != 5:
            _fail(f"gate_framediff must be [T,V,1,Hf,Wf], got shape={gate.shape}")
        save_obj["gate_framediff"] = gate.astype(target_dtype, copy=False)
    if "token_layer_idx" in extras:
        save_obj["token_layer_idx"] = np.int64(int(extras["token_layer_idx"]))
    if "token_proj_dim" in extras:
        save_obj["token_proj_dim"] = np.int64(int(extras["token_proj_dim"]))
    if "token_proj_seed" in extras:
        save_obj["token_proj_seed"] = np.int64(int(extras["token_proj_seed"]))
    if "phi_is_normalized" in extras:
        save_obj["phi_is_normalized"] = np.int64(1 if bool(extras["phi_is_normalized"]) else 0)

    np.savez_compressed(npz_path, **save_obj)

    meta = {
        "data_dir": str(data_dir),
        "out_dir": str(out_dir),
        "backend": args.backend,
        "camera_names": camera_names,
        "frame_start": int(args.frame_start),
        "num_frames": int(args.num_frames),
        "phi_name": args.phi_name,
        "vggt_mode": args.vggt_mode,
        "input_size": [int(x) for x in input_size],
        "phi_size": [int(x) for x in phi_size],
        "phi_shape": [int(x) for x in phi.shape],
        "dtype": args.dtype,
        "has_conf": conf is not None,
        "has_gate_framediff": "gate_framediff" in save_obj,
        "framediff_top_p": (
            float(extras.get("framediff_top_p")) if "framediff_top_p" in extras else None
        ),
        "phi_is_normalized": bool(extras.get("phi_is_normalized", False)),
    }
    if "token_layer_idx" in extras:
        meta["token_layer_idx"] = int(extras["token_layer_idx"])
    if "token_proj_dim" in extras:
        meta["token_proj_dim"] = int(extras["token_proj_dim"])
    if "token_proj_seed" in extras:
        meta["token_proj_seed"] = int(extras["token_proj_seed"])
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[VGGTCache] wrote {npz_path}")
    print(f"[VGGTCache] wrote {meta_path}")
    print(
        f"[VGGTCache] phi shape={tuple(phi.shape)} dtype={phi.dtype} "
        f"input_size={input_size} phi_size={phi_size}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
