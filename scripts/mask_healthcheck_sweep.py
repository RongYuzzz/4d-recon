#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _fail(msg: str) -> None:
    raise SystemExit(f"[MaskHealthcheck][ERROR] {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Sweep pred thresholds and report mIoU/top-p overlap vs GT silhouette."
    )
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--pred_mask_npz", required=True, help="pseudo_masks.npz")
    ap.add_argument("--camera", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--thr_gt", type=float, default=0.5)
    ap.add_argument("--thr_pred_list", default="0.01,0.02,0.05,0.1,0.2,0.5")
    ap.add_argument("--top_p_list", default="0.01,0.05,0.1")
    return ap.parse_args()


def _load_mask01(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        m = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    return np.clip(m, 0.0, 1.0)


def _load_pred01_tv(pred_npz: Path, camera: str) -> np.ndarray:
    with np.load(pred_npz, allow_pickle=True) as d:
        masks = np.asarray(d["masks"])
        cams = [str(x) for x in d["camera_names"].tolist()]
        if camera not in cams:
            _fail(f"camera not found in npz: {camera} not in {cams}")
        vi = cams.index(camera)
        m = masks[:, vi].astype(np.float32)
        if float(m.max()) > 1.0:
            m = m / 255.0
        return np.clip(m, 0.0, 1.0)


def _resize_pred_to_gt(pred01_small: np.ndarray, hw: tuple[int, int]) -> np.ndarray:
    h, w = hw
    out = np.empty((pred01_small.shape[0], h, w), dtype=np.float32)
    for t in range(pred01_small.shape[0]):
        im = Image.fromarray((pred01_small[t] * 255.0).astype(np.uint8), mode="L")
        im = im.resize((w, h), resample=Image.Resampling.BILINEAR)
        out[t] = np.asarray(im, dtype=np.float32) / 255.0
    return np.clip(out, 0.0, 1.0)


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir).resolve()
    pred_npz = Path(args.pred_mask_npz).resolve()
    out_json = Path(args.out_json).resolve()
    cam = str(args.camera)

    gt_dir = data_dir / "masks" / cam
    if not gt_dir.is_dir():
        _fail(f"missing GT mask dir: {gt_dir}")
    if not pred_npz.exists():
        _fail(f"missing pred_mask_npz: {pred_npz}")

    pred_small = _load_pred01_tv(pred_npz, camera=cam)
    num_frames = int(pred_small.shape[0])
    gt0 = _load_mask01(gt_dir / f"{0:06d}.png")
    pred = _resize_pred_to_gt(pred_small, hw=gt0.shape[:2])

    gt = []
    for t in range(num_frames):
        p = gt_dir / f"{t:06d}.png"
        if not p.exists():
            _fail(f"missing GT mask frame: {p}")
        gt.append(_load_mask01(p))
    gt = np.stack(gt, axis=0)
    gt_bin = gt > float(args.thr_gt)

    thr_list = [float(x) for x in args.thr_pred_list.split(",") if x.strip()]
    top_p_list = [float(x) for x in args.top_p_list.split(",") if x.strip()]

    def miou_for_thr(thr: float) -> float:
        ious = []
        for t in range(num_frames):
            pb = pred[t] > thr
            gb = gt_bin[t]
            inter = float(np.logical_and(pb, gb).sum())
            union = float(np.logical_or(pb, gb).sum())
            if union > 0:
                ious.append(inter / union)
        return float(np.mean(ious)) if ious else float("nan")

    best_thr = None
    best_miou = -1.0
    for thr in thr_list:
        m = miou_for_thr(thr)
        if np.isfinite(m) and m > best_miou:
            best_miou = float(m)
            best_thr = float(thr)

    top_p_overlap: dict[str, float] = {}
    for p in top_p_list:
        if p <= 0 or p > 1:
            continue
        overlaps = []
        for t in range(num_frames):
            flat = pred[t].reshape(-1)
            k = max(1, int(np.ceil(p * flat.size)))
            idx = np.argpartition(flat, -k)[-k:]
            topk = np.zeros_like(flat, dtype=bool)
            topk[idx] = True
            gb = gt_bin[t].reshape(-1)
            inter = float(np.logical_and(topk, gb).sum())
            denom = float(np.sum(topk)) if float(np.sum(topk)) > 0 else 1.0
            overlaps.append(inter / denom)
        top_p_overlap[f"{p:g}"] = float(np.mean(overlaps)) if overlaps else float("nan")

    out: dict[str, Any] = {
        "camera": cam,
        "num_frames": num_frames,
        "thr_gt": float(args.thr_gt),
        "thr_pred_list": thr_list,
        "best_miou_fg": float(best_miou),
        "best_thr_pred": float(best_thr) if best_thr is not None else None,
        "top_p_overlap": top_p_overlap,
        "pred_mask_npz": str(pred_npz),
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"[MaskHealthcheck] wrote: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
