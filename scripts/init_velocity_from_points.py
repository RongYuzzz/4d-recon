#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np


def _try_import_ckdtree():
    try:
        from scipy.spatial import cKDTree  # type: ignore
    except Exception:  # noqa: BLE001
        cKDTree = None  # type: ignore[assignment]
    return cKDTree


def _load_points(triangulation_dir: Path, frame: int) -> np.ndarray | None:
    path = triangulation_dir / f"points3d_frame{frame:06d}.npy"
    if not path.exists():
        return None
    arr = np.load(path)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(f"invalid points array: {path} shape={arr.shape}")
    return arr.astype(np.float32, copy=False)


def _percentiles(x: np.ndarray, ps: list[float]) -> dict[str, float]:
    if x.size == 0:
        return {f"p{int(p*100):02d}": float("nan") for p in ps}
    out = {}
    for p in ps:
        out[f"p{int(p*100):02d}"] = float(np.quantile(x, p))
    return out


def _mag(x: np.ndarray) -> np.ndarray:
    return np.linalg.norm(x, axis=1)


def _tree_query(tree, pts: np.ndarray, workers: int) -> tuple[np.ndarray, np.ndarray]:
    # SciPy cKDTree uses `workers=` (newer) or no parallel arg (older).
    try:
        dist, idx = tree.query(pts, k=1, workers=workers)
    except TypeError:
        dist, idx = tree.query(pts, k=1)
    return dist.astype(np.float32, copy=False), idx.astype(np.int64, copy=False)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Plan-B: estimate 3D velocity init from per-frame triangulation points.")
    ap.add_argument("--data_dir", required=True, help="Dataset root containing triangulation/*.npy")
    ap.add_argument("--baseline_init_npz", required=True, help="Baseline keyframes_*.npz (template for schema)")
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--frame_end_exclusive", type=int, default=60)
    ap.add_argument("--keyframe_step", type=int, default=5)
    ap.add_argument("--max_match_distance", type=float, default=0.5)
    ap.add_argument("--no_mutual_nn", action="store_true", help="Disable mutual-NN filtering (not recommended)")
    ap.add_argument("--disable_drift_removal", action="store_true", help="Disable per-pair median drift removal")
    ap.add_argument("--clip_quantile", type=float, default=0.99, help="Clip ||v|| at this quantile (valid matches only)")
    ap.add_argument("--zero_eps", type=float, default=1e-4, help="Eps for ratio(||v|| < eps)")
    ap.add_argument("--workers", type=int, default=-1, help="KDTree workers (-1=all cores when supported)")
    ap.add_argument(
        "--out_dir",
        default="",
        help="Output directory (default: <repo>/outputs/plan_b/<data_dir_basename>)",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    data_dir = Path(args.data_dir).resolve()
    tri_dir = data_dir / "triangulation"
    if not tri_dir.is_dir():
        raise SystemExit(f"[ERROR] missing triangulation dir: {tri_dir}")

    baseline_npz = Path(args.baseline_init_npz).resolve()
    if not baseline_npz.is_file():
        raise SystemExit(f"[ERROR] missing baseline init npz: {baseline_npz}")

    frame_start = int(args.frame_start)
    frame_end_excl = int(args.frame_end_exclusive)
    keyframe_step = int(args.keyframe_step)
    if frame_end_excl <= frame_start + 1:
        raise SystemExit(f"[ERROR] invalid frame range: start={frame_start} end={frame_end_excl}")
    if keyframe_step <= 0 or keyframe_step >= (frame_end_excl - frame_start):
        raise SystemExit(f"[ERROR] invalid keyframe_step={keyframe_step} for range [{frame_start},{frame_end_excl})")

    total_frames = frame_end_excl - frame_start
    keyframes = list(range(frame_start, frame_end_excl, keyframe_step))

    # Resolve default out dir relative to repo root (this script lives in <repo>/scripts).
    if args.out_dir:
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = (Path(__file__).resolve().parents[1] / out_dir).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[1]
        out_dir = repo_root / "outputs" / "plan_b" / data_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)

    out_npz = out_dir / f"init_points_planb_step{keyframe_step}.npz"
    out_stats = out_dir / "velocity_stats.json"

    cKDTree = _try_import_ckdtree()
    if cKDTree is None:
        raise SystemExit(
            "[ERROR] scipy.spatial.cKDTree is not available. "
            "Run with the FreeTimeGsVanilla venv python or install scipy."
        )

    data = np.load(baseline_npz, allow_pickle=False)
    required = ("positions", "velocities", "colors", "times")
    for k in required:
        if k not in data:
            raise SystemExit(f"[ERROR] baseline init npz missing key: {k}")

    positions = data["positions"].astype(np.float32, copy=False)
    colors = data["colors"].astype(np.float32, copy=False)
    times_raw = data["times"]
    times = times_raw.flatten().astype(np.float32, copy=False)
    durations_raw = data["durations"] if "durations" in data else (np.ones((len(times), 1), dtype=np.float32) * 0.1)
    durations = durations_raw  # keep raw shape for saving

    n_total = int(positions.shape[0])
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise SystemExit(f"[ERROR] invalid positions shape: {positions.shape}")
    if colors.ndim != 2 or colors.shape[1] != 3 or colors.shape[0] != n_total:
        raise SystemExit(f"[ERROR] invalid colors shape: {colors.shape}")
    if times.shape[0] != n_total:
        raise SystemExit(f"[ERROR] invalid times shape: {times_raw.shape} -> {times.shape}")

    # Map each point to its keyframe index via the same convention as combine_frames_fast_keyframes:
    # t = (frame - frame_start) / total_frames (NOT total_frames-1).
    frames_of_point = np.rint(times * float(total_frames)).astype(np.int32) + frame_start

    # Build index lists for each keyframe.
    idx_by_keyframe: dict[int, np.ndarray] = {}
    for kf in keyframes:
        idx = np.nonzero(frames_of_point == kf)[0]
        if idx.size:
            idx_by_keyframe[kf] = idx

    velocities_out = np.zeros((n_total, 3), dtype=np.float32)
    has_velocity_out = np.zeros((n_total,), dtype=bool)

    per_pair: list[dict[str, Any]] = []
    eligible_points = 0
    total_valid = 0

    max_dist = float(args.max_match_distance)
    use_mutual = not bool(args.no_mutual_nn)
    drift_removal = not bool(args.disable_drift_removal)
    workers = int(args.workers)

    for kf in keyframes:
        idx = idx_by_keyframe.get(kf)
        if idx is None:
            continue

        next_frame = kf + keyframe_step
        rec: dict[str, Any] = {
            "keyframe": int(kf),
            "next_frame": int(next_frame),
            "n_points": int(idx.size),
        }

        if next_frame >= frame_end_excl:
            rec.update({"status": "no_next_frame", "n_valid": 0, "match_ratio": 0.0})
            per_pair.append(rec)
            continue

        pos_next = _load_points(tri_dir, next_frame)
        if pos_next is None or pos_next.size == 0:
            rec.update({"status": "missing_next_points", "n_valid": 0, "match_ratio": 0.0})
            per_pair.append(rec)
            eligible_points += int(idx.size)
            continue

        pos_t = positions[idx]
        eligible_points += int(idx.size)

        tree_next = cKDTree(pos_next, balanced_tree=True, compact_nodes=True)
        dist_fwd, nn_fwd = _tree_query(tree_next, pos_t, workers=workers)

        valid = dist_fwd <= max_dist
        if use_mutual:
            tree_t = cKDTree(pos_t, balanced_tree=True, compact_nodes=True)
            _, nn_rev = _tree_query(tree_t, pos_next, workers=workers)
            # mutual: pos_next[nn_fwd[i]] points back to i
            mutual = nn_rev[nn_fwd] == np.arange(pos_t.shape[0])
            valid &= mutual

        n_valid = int(valid.sum())
        total_valid += n_valid
        rec["n_valid"] = n_valid
        rec["match_ratio"] = float(n_valid / max(1, pos_t.shape[0]))
        rec["status"] = "ok"

        if n_valid == 0:
            per_pair.append(rec)
            continue

        j = nn_fwd[valid]
        disp = pos_next[j] - pos_t[valid]  # [n_valid, 3]

        drift = np.zeros((3,), dtype=np.float32)
        if drift_removal:
            drift = np.median(disp, axis=0).astype(np.float32, copy=False)
            disp = disp - drift

        v = disp / float(keyframe_step)  # meters/frame (RAW); trainer will scale by total_frames

        # Write into output buffers
        out_idx = idx[valid]
        velocities_out[out_idx] = v.astype(np.float32, copy=False)
        has_velocity_out[out_idx] = True

        rec["drift_median"] = [float(x) for x in drift.tolist()]
        rec["drift_mag"] = float(np.linalg.norm(drift))
        vmag = _mag(v)
        rec["vel_mag_mean"] = float(vmag.mean())
        rec["vel_mag_max"] = float(vmag.max())
        rec.update(_percentiles(vmag, [0.5, 0.9, 0.99]))
        per_pair.append(rec)

    # Global clip (valid matches only)
    clip_q = float(args.clip_quantile)
    vmag_valid = _mag(velocities_out[has_velocity_out])
    clip_thr = float("nan")
    n_clipped = 0
    if vmag_valid.size and 0.0 < clip_q <= 1.0:
        clip_thr = float(np.quantile(vmag_valid, clip_q))
        if clip_thr > 0:
            mags = _mag(velocities_out)
            to_clip = has_velocity_out & (mags > clip_thr)
            if to_clip.any():
                scale = (clip_thr / (mags[to_clip] + 1e-8)).astype(np.float32)
                velocities_out[to_clip] *= scale[:, None]
                n_clipped = int(to_clip.sum())

    vel_mag_all = _mag(velocities_out)
    vel_mag_valid2 = _mag(velocities_out[has_velocity_out])

    def _ratio_lt(x: np.ndarray, eps: float) -> float:
        if x.size == 0:
            return float("nan")
        return float((x < eps).mean())

    stats: dict[str, Any] = {
        "data_dir": str(data_dir),
        "triangulation_dir": str(tri_dir),
        "baseline_init_npz": str(baseline_npz),
        "out_npz": str(out_npz),
        "frame_start": frame_start,
        "frame_end_exclusive": frame_end_excl,
        "total_frames": total_frames,
        "keyframe_step": keyframe_step,
        "max_match_distance": max_dist,
        "mutual_nn": use_mutual,
        "drift_removal": drift_removal,
        "clip_quantile": clip_q,
        "clip_threshold_m_per_frame": clip_thr,
        "n_clipped": n_clipped,
        "units": {
            "velocities_out_npz": "meters_per_frame (RAW); trainer scales by total_frames to meters_per_normalized_time",
            "trainer_scaling_note": "trainer uses v_scaled = v_raw * (frame_end_exclusive-frame_start) for normalized time",
        },
        "counts": {
            "n_total_points": n_total,
            "n_points_with_next_frame": int(eligible_points),
            "n_valid_matches": int(total_valid),
            "match_ratio_over_eligible": float(total_valid / max(1, eligible_points)),
            "match_ratio_over_all": float(total_valid / max(1, n_total)),
        },
        "vel_mag_m_per_frame": {
            "all": {
                "mean": float(vel_mag_all.mean()) if vel_mag_all.size else float("nan"),
                "max": float(vel_mag_all.max()) if vel_mag_all.size else float("nan"),
                "ratio_lt_eps": _ratio_lt(vel_mag_all, float(args.zero_eps)),
            },
            "valid": {
                "mean": float(vel_mag_valid2.mean()) if vel_mag_valid2.size else float("nan"),
                "max": float(vel_mag_valid2.max()) if vel_mag_valid2.size else float("nan"),
                "ratio_lt_eps": _ratio_lt(vel_mag_valid2, float(args.zero_eps)),
                **_percentiles(vel_mag_valid2, [0.5, 0.9, 0.99]),
            },
        },
        "per_pair": per_pair,
    }

    out_stats.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Save npz: preserve baseline schema, only replace velocities (+has_velocity) and add planb metadata keys.
    save_obj: dict[str, Any] = {}
    for k in data.files:
        if k in {"velocities", "has_velocity"}:
            continue
        save_obj[k] = data[k]
    save_obj["positions"] = positions
    save_obj["colors"] = colors
    save_obj["times"] = times_raw
    save_obj["durations"] = durations
    save_obj["velocities"] = velocities_out
    save_obj["has_velocity"] = has_velocity_out
    save_obj["planb_source_init_npz"] = np.array(str(baseline_npz))
    save_obj["planb_method"] = np.array("mutual_nn_knn_drift_clip")
    save_obj["planb_keyframe_step"] = np.array(keyframe_step, dtype=np.int32)
    save_obj["planb_max_match_distance"] = np.array(max_dist, dtype=np.float32)
    save_obj["planb_clip_quantile"] = np.array(clip_q, dtype=np.float32)
    save_obj["planb_clip_threshold_m_per_frame"] = np.array(clip_thr, dtype=np.float32)

    np.savez_compressed(out_npz, **save_obj)

    print("[Plan-B] wrote:", out_npz)
    print("[Plan-B] wrote:", out_stats)
    print("[Plan-B] match_ratio_over_eligible:", f"{stats['counts']['match_ratio_over_eligible']:.4f}")
    print("[Plan-B] v_valid mean/max (m/frame):", f"{stats['vel_mag_m_per_frame']['valid']['mean']:.6f}", "/", f"{stats['vel_mag_m_per_frame']['valid']['max']:.6f}")
    if not math.isnan(clip_thr):
        print("[Plan-B] clip_threshold (m/frame):", f"{clip_thr:.6f}", f"(q={clip_q})", "clipped:", n_clipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

