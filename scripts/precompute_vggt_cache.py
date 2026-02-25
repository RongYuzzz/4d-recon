#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
) -> tuple[np.ndarray, np.ndarray | None, list[int], list[int]]:
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
    return phi, None, input_size, phi_size


def _run_backend_vggt(
    frame_maps: dict[str, dict[int, Path]],
    camera_names: list[str],
    frame_indices: list[int],
    phi_name: str,
    vggt_model_id: str,
    vggt_cache_dir: str,
    vggt_mode: str,
    phi_downscale: int,
) -> tuple[np.ndarray, np.ndarray | None, list[int], list[int]]:
    try:
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images
    except Exception as exc:  # noqa: BLE001
        _fail(
            "backend=vggt requires VGGT package. "
            "Install with: pip install 'git+https://github.com/facebookresearch/vggt.git'. "
            f"import error: {exc}"
        )

    if phi_name not in {"depth", "world_points"}:
        _fail(f"--phi_name for backend=vggt must be one of depth|world_points, got {phi_name}")
    if vggt_mode not in {"crop", "pad"}:
        _fail(f"--vggt_mode must be crop|pad, got {vggt_mode}")
    if not vggt_model_id.strip():
        _fail("--vggt_model_id must be non-empty")

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
    input_size: list[int] | None = None
    phi_size: list[int] | None = None
    num_views = len(camera_names)

    for i, frame_idx in enumerate(frame_indices):
        image_paths = [str(frame_maps[cam][frame_idx]) for cam in camera_names]
        images = load_and_preprocess_images(image_paths, mode=vggt_mode).to(device)
        if images.ndim < 4:
            _fail(f"unexpected preprocessed image tensor shape: {tuple(images.shape)}")
        if input_size is None:
            input_size = [int(images.shape[-2]), int(images.shape[-1])]

        with torch.no_grad():
            if device == "cuda":
                with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
                    pred = model(images)
            else:
                pred = model(images)

        if phi_name not in pred:
            _fail(f"VGGT output missing key '{phi_name}'")
        phi_vchw = _to_vchw(pred[phi_name], num_views=num_views, key=phi_name)
        phi_vchw = _downscale_vchw(phi_vchw, phi_downscale)
        if phi_size is None:
            phi_size = [int(phi_vchw.shape[-2]), int(phi_vchw.shape[-1])]
        phi_frames.append(phi_vchw.astype(np.float32, copy=False))

        if phi_name == "depth" and "depth_conf" in pred:
            conf_vchw = _to_vchw(pred["depth_conf"], num_views=num_views, key="depth_conf")
            conf_vchw = _downscale_vchw(conf_vchw, phi_downscale)
            conf_frames.append(np.clip(conf_vchw, 0.0, 1.0).astype(np.float32, copy=False))

        if i == 0 or i == len(frame_indices) - 1 or (i + 1) % 10 == 0:
            print(f"[VGGTCache] processed frame {i + 1}/{len(frame_indices)}")

        del images, pred
        if device == "cuda":
            torch.cuda.empty_cache()

    if input_size is None or phi_size is None:
        _fail("no frames generated for vggt backend")

    phi = np.stack(phi_frames, axis=0).astype(np.float32, copy=False)
    conf = None
    if conf_frames:
        conf = np.stack(conf_frames, axis=0).astype(np.float32, copy=False)
    return phi, conf, input_size, phi_size


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
    ap.add_argument("--phi_name", default="depth", help="dummy_rgb or VGGT key depth|world_points")
    ap.add_argument("--phi_downscale", type=int, default=4, help="Downscale factor in phi-space")
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

    if args.backend == "dummy":
        phi, conf, input_size, phi_size = _run_backend_dummy(
            frame_maps=frame_maps,
            camera_names=camera_names,
            frame_indices=frame_indices,
            phi_downscale=args.phi_downscale,
        )
    else:
        phi, conf, input_size, phi_size = _run_backend_vggt(
            frame_maps=frame_maps,
            camera_names=camera_names,
            frame_indices=frame_indices,
            phi_name=args.phi_name,
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
    }
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
