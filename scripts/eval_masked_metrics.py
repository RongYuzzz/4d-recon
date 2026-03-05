#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[EvalMaskedMetrics][ERROR] {msg}")


def _load_rgb01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def _load_mask01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        mask = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    return np.clip(mask, 0.0, 1.0)


def _psnr(a01: np.ndarray, b01: np.ndarray) -> float:
    diff = (a01.astype(np.float32) - b01.astype(np.float32)).reshape(-1)
    mse = float(np.mean(diff * diff))
    if mse <= 1e-12:
        return 99.0
    return 10.0 * math.log10(1.0 / mse)


def _psnr_mask_area(pred01: np.ndarray, gt01: np.ndarray, keep01: np.ndarray) -> float:
    # keep01: [H,W,1] in {0,1}
    diff = (pred01.astype(np.float32) - gt01.astype(np.float32)) * keep01.astype(np.float32)
    denom = float(np.sum(keep01)) * 3.0
    if denom <= 1e-12:
        return float("nan")
    mse = float(np.sum(diff * diff) / denom)
    if mse <= 1e-12:
        return 99.0
    return 10.0 * math.log10(1.0 / mse)


class _LPIPS:
    def __init__(self, backend: str):
        self.backend = backend
        self._model = None
        self._torch = None
        self._device = "cpu"

        if backend in {"none", "dummy"}:
            return
        if backend != "auto":
            _fail(f"unsupported lpips_backend: {backend}")
        try:
            import lpips  # type: ignore
            import torch  # type: ignore
        except Exception as exc:  # noqa: BLE001
            _fail(f"lpips_backend=auto requires torch+lpips installed: {exc}")

        self._torch = torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = lpips.LPIPS(net="alex").to(self._device).eval()

    def __call__(self, a01: np.ndarray, b01: np.ndarray) -> float | None:
        if self.backend == "none":
            return None
        if self.backend == "dummy":
            return float(np.mean(np.abs(a01.astype(np.float32) - b01.astype(np.float32))))

        assert self._torch is not None and self._model is not None
        torch = self._torch
        a = torch.from_numpy(a01.transpose(2, 0, 1)[None, ...]).to(self._device)
        b = torch.from_numpy(b01.transpose(2, 0, 1)[None, ...]).to(self._device)
        a = a * 2.0 - 1.0
        b = b * 2.0 - 1.0
        with torch.no_grad():
            value = self._model(a, b)
        return float(value.detach().float().cpu().item())


def _read_cfg_scalars(cfg_path: Path) -> dict[str, str]:
    scalars: dict[str, str] = {}
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("- ") or raw.startswith("!!python"):
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            scalars[key] = value
    return scalars


@dataclass(frozen=True)
class _BBox:
    x0: int
    y0: int
    x1: int
    y1: int


def _bbox_from_mask(mask01: np.ndarray, thr: float, margin: int) -> _BBox | None:
    mask_bin = mask01 > float(thr)
    if not bool(np.any(mask_bin)):
        return None
    ys, xs = np.where(mask_bin)
    y0 = max(0, int(ys.min()) - margin)
    y1 = min(int(mask01.shape[0]), int(ys.max()) + 1 + margin)
    x0 = max(0, int(xs.min()) - margin)
    x1 = min(int(mask01.shape[1]), int(xs.max()) + 1 + margin)
    if x1 <= x0 or y1 <= y0:
        return None
    return _BBox(x0=x0, y0=y0, x1=x1, y1=y1)


_RENDER_RE = re.compile(r"^(val|test)_step(\d+)_([0-9]{4})\.png$")


def _list_renders(renders_dir: Path, stage: str, step: int) -> list[Path]:
    prefix = f"{stage}_step{step}_"
    files = [
        path
        for path in renders_dir.iterdir()
        if path.is_file() and path.name.startswith(prefix) and path.suffix.lower() == ".png"
    ]

    def _index(path: Path) -> int:
        match = _RENDER_RE.match(path.name)
        if not match:
            return 10**9
        return int(match.group(3))

    return sorted(files, key=_index)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute foreground-masked PSNR/LPIPS from trainer renders + dataset masks."
    )
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--result_dir", required=True)
    parser.add_argument("--stage", choices=["val", "test"], required=True)
    parser.add_argument("--step", type=int, required=True, help="Trainer step, e.g. 599")
    parser.add_argument(
        "--mask_source",
        choices=["dataset", "pseudo_mask", "none"],
        default="dataset",
    )
    parser.add_argument(
        "--pred_mask_npz",
        default="",
        help="pseudo_masks.npz (required when mask_source=pseudo_mask or when computing miou_fg)",
    )
    parser.add_argument("--bbox_margin_px", type=int, default=32)
    parser.add_argument(
        "--mask_thr",
        type=float,
        default=0.5,
        help="Threshold to derive binary mask for bbox+fill-black",
    )
    parser.add_argument("--lpips_backend", choices=["auto", "dummy", "none"], default="auto")
    parser.add_argument(
        "--compute_miou",
        action="store_true",
        help="Compute miou_fg when both GT and pred masks are available",
    )
    return parser.parse_args()


def _load_pred_mask_tv(pred_npz: Path, camera: str, t_local: int) -> np.ndarray:
    with np.load(pred_npz, allow_pickle=True) as data:
        masks = np.asarray(data["masks"])
        cameras = [str(item) for item in data["camera_names"].tolist()]
        _ = int(data["frame_start"])
        if t_local < 0 or t_local >= int(data["num_frames"]):
            _fail(f"t_local out of range for pred masks: {t_local}")
        if camera not in cameras:
            _fail(f"camera '{camera}' not found in pred mask npz cameras={cameras}")
        view_idx = cameras.index(camera)
        mask = masks[t_local, view_idx].astype(np.float32)
        if float(mask.max()) > 1.0:
            mask = mask / 255.0
        return np.clip(mask, 0.0, 1.0)


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    result_dir = Path(args.result_dir).resolve()
    stage = str(args.stage)
    step = int(args.step)
    margin = int(args.bbox_margin_px)

    cfg_path = result_dir / "cfg.yml"
    if not cfg_path.exists():
        _fail(f"missing cfg.yml: {cfg_path}")
    cfg = _read_cfg_scalars(cfg_path)

    start_frame = int(cfg.get("start_frame", "0"))
    end_frame = int(cfg.get("end_frame", "0"))
    if end_frame <= start_frame:
        _fail(f"invalid frame range in cfg.yml: start={start_frame} end={end_frame}")
    num_frames = end_frame - start_frame

    if stage == "test":
        camera = cfg.get("test_camera_names", "").strip()
        sample_every = int(cfg.get("eval_sample_every_test", "1"))
    else:
        camera = cfg.get("val_camera_names", "").strip()
        sample_every = int(cfg.get("eval_sample_every", "1"))
    if not camera or "," in camera:
        _fail(f"evaluator expects single {stage} camera; got: '{camera}'")
    if sample_every <= 0:
        _fail(f"invalid eval_sample_every: {sample_every}")

    gt_mask_dir = data_dir / "masks" / camera
    renders_dir = result_dir / "renders"
    stats_in = result_dir / "stats" / f"{stage}_step{step:04d}.json"

    render_files = _list_renders(renders_dir, stage=stage, step=step)
    frame_indices = list(range(start_frame, end_frame, sample_every))
    if len(render_files) != len(frame_indices):
        _fail(
            f"render count mismatch: renders={len(render_files)} vs expected_frames={len(frame_indices)} "
            f"(start={start_frame} end={end_frame} every={sample_every})"
        )

    pred_npz = Path(args.pred_mask_npz).resolve() if args.pred_mask_npz else None
    if args.mask_source == "pseudo_mask" and pred_npz is None:
        _fail("--pred_mask_npz required when --mask_source=pseudo_mask")

    lpips_fn = _LPIPS(args.lpips_backend)
    psnr_list: list[float] = []
    psnr_area_list: list[float] = []
    lpips_list: list[float] = []
    lpips_comp_list: list[float] = []
    iou_list: list[float] = []

    for frame_idx, render_path in zip(frame_indices, render_files):
        frame_offset = frame_idx - start_frame
        canvas = _load_rgb01(render_path)
        if canvas.shape[1] % 2 != 0:
            _fail(
                f"expected concat render canvas (GT|Pred) with even width; got {canvas.shape} at {render_path}"
            )

        width = canvas.shape[1] // 2
        gt = canvas[:, :width, :]
        pred = canvas[:, width:, :]
        if gt.shape != pred.shape:
            _fail(f"unexpected split shapes gt={gt.shape} pred={pred.shape} for {render_path}")

        if args.mask_source == "none":
            continue

        if args.mask_source == "dataset":
            mask_path = gt_mask_dir / f"{frame_offset:06d}.png"
            if not mask_path.exists():
                _fail(f"missing GT mask: {mask_path}")
            mask01 = _load_mask01(mask_path)
        else:
            assert pred_npz is not None
            pred_small = _load_pred_mask_tv(pred_npz, camera=camera, t_local=frame_offset)
            mask_img = Image.fromarray((pred_small * 255.0).astype(np.uint8), mode="L")
            mask_img = mask_img.resize((gt.shape[1], gt.shape[0]), resample=Image.Resampling.BILINEAR)
            mask01 = np.asarray(mask_img, dtype=np.float32) / 255.0

        if mask01.shape[:2] != gt.shape[:2]:
            _fail(
                f"mask/gt shape mismatch: mask={mask01.shape} gt={gt.shape} "
                "(did you downscale masks with images?)"
            )

        keep_full = (mask01 > float(args.mask_thr)).astype(np.float32)[..., None]
        bbox = _bbox_from_mask(mask01, thr=float(args.mask_thr), margin=margin)
        if bbox is None:
            continue

        gt_crop = gt[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1].copy()
        pred_crop = pred[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1].copy()
        mask_crop = mask01[bbox.y0 : bbox.y1, bbox.x0 : bbox.x1]
        keep = (mask_crop > float(args.mask_thr)).astype(np.float32)[..., None]
        gt_crop *= keep
        pred_crop *= keep

        psnr_list.append(_psnr(pred_crop, gt_crop))
        psnr_area_list.append(_psnr_mask_area(pred_crop, gt_crop, keep))
        value_lpips = lpips_fn(pred_crop, gt_crop)
        if value_lpips is not None:
            lpips_list.append(float(value_lpips))
        pred_comp = pred * keep_full + gt * (1.0 - keep_full)
        value_lpips_comp = lpips_fn(pred_comp, gt)
        if value_lpips_comp is not None:
            lpips_comp_list.append(float(value_lpips_comp))

        if args.compute_miou:
            if pred_npz is None:
                _fail("--pred_mask_npz required when --compute_miou")
            if args.mask_source != "dataset":
                _fail("--compute_miou requires --mask_source=dataset (GT mask provides gt_fg)")
            gt_bin = mask01 > float(args.mask_thr)
            pred_small = _load_pred_mask_tv(pred_npz, camera=camera, t_local=frame_offset)
            pred_img = Image.fromarray((pred_small * 255.0).astype(np.uint8), mode="L")
            pred_img = pred_img.resize((gt.shape[1], gt.shape[0]), resample=Image.Resampling.BILINEAR)
            pred01 = np.asarray(pred_img, dtype=np.float32) / 255.0
            pred_bin = pred01 > float(args.mask_thr)
            inter = float(np.logical_and(gt_bin, pred_bin).sum())
            union = float(np.logical_or(gt_bin, pred_bin).sum())
            if union > 0:
                iou_list.append(inter / union)

    base_stats: dict[str, Any] = {}
    if stats_in.exists():
        try:
            base_stats = json.loads(stats_in.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            base_stats = {}

    out = {
        "stage": stage,
        "step": step,
        "mask_source": args.mask_source,
        "bbox_margin_px": margin,
        "mask_thr": float(args.mask_thr),
        "lpips_backend": args.lpips_backend,
        "psnr": base_stats.get("psnr", ""),
        "ssim": base_stats.get("ssim", ""),
        "lpips": base_stats.get("lpips", ""),
        "tlpips": base_stats.get("tlpips", ""),
        "psnr_fg": float(np.mean(psnr_list)) if psnr_list else float("nan"),
        "lpips_fg": float(np.mean(lpips_list)) if lpips_list else float("nan"),
        "psnr_fg_area": float(np.nanmean(psnr_area_list)) if psnr_area_list else float("nan"),
        "lpips_fg_comp": float(np.mean(lpips_comp_list)) if lpips_comp_list else float("nan"),
        "num_fg_frames": int(len(psnr_list)),
        "num_frames": int(num_frames),
    }
    if iou_list:
        out["miou_fg"] = float(np.mean(iou_list))

    out_dir = result_dir / "stats_masked"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stage}_step{step:04d}.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"[EvalMaskedMetrics] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
