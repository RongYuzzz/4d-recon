#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch


def _fail(message: str) -> None:
    raise RuntimeError(message)


def _as_numpy(value: object, name: str) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value
    if torch.is_tensor(value):
        return value.detach().cpu().numpy()
    _fail(f"{name} must be numpy array or torch tensor, got {type(value)}")


def _stats_1d(values: np.ndarray) -> dict[str, float]:
    if values.ndim != 1:
        _fail(f"expected 1D array, got shape={values.shape}")
    if values.size == 0:
        _fail("stats input is empty")
    return {
        "min": float(np.min(values)),
        "mean": float(np.mean(values)),
        "p50": float(np.percentile(values, 50.0)),
        "p90": float(np.percentile(values, 90.0)),
        "p99": float(np.percentile(values, 99.0)),
        "max": float(np.max(values)),
    }


def _stats_min_mean_max(values: np.ndarray) -> dict[str, float]:
    if values.ndim != 1:
        _fail(f"expected 1D array, got shape={values.shape}")
    if values.size == 0:
        _fail("stats input is empty")
    return {
        "min": float(np.min(values)),
        "mean": float(np.mean(values)),
        "max": float(np.max(values)),
    }


def _velocity_summary(velocities: np.ndarray, eps: float) -> tuple[dict[str, float], float]:
    if velocities.ndim != 2 or velocities.shape[1] != 3:
        _fail(f"velocities must have shape [N,3], got {velocities.shape}")
    speed = np.linalg.norm(velocities.astype(np.float64, copy=False), axis=1)
    stats = _stats_1d(speed)
    ratio = float(np.mean(speed < float(eps)))
    return stats, ratio


def _load_init_npz(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not path.exists():
        _fail(f"init npz not found: {path}")
    with np.load(path, allow_pickle=True) as z:
        for key in ("velocities", "times", "durations"):
            if key not in z:
                _fail(f"init npz missing key: {key}")
        velocities = np.asarray(z["velocities"], dtype=np.float64)
        times = np.asarray(z["times"], dtype=np.float64).reshape(-1)
        durations = np.asarray(z["durations"], dtype=np.float64).reshape(-1)
    return velocities, times, durations


def _load_ckpt(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if not path.exists():
        _fail(f"checkpoint not found: {path}")
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(ckpt, dict):
        _fail(f"checkpoint root must be dict, got {type(ckpt)}")
    if "splats" not in ckpt:
        _fail("checkpoint missing key: splats")
    splats = ckpt["splats"]
    if not isinstance(splats, dict):
        _fail(f"checkpoint splats must be dict, got {type(splats)}")
    for key in ("velocities", "times", "durations"):
        if key not in splats:
            _fail(f"checkpoint splats missing key: {key}")

    velocities = _as_numpy(splats["velocities"], "splats.velocities").astype(np.float64, copy=False)
    times = _as_numpy(splats["times"], "splats.times").astype(np.float64, copy=False).reshape(-1)
    # Trainer stores log-duration in checkpoint; convert back to original duration space.
    durations_log = _as_numpy(splats["durations"], "splats.durations").astype(np.float64, copy=False)
    durations = np.exp(durations_log.reshape(-1))
    return velocities, times, durations


def _format_stats_row(stats: dict[str, float]) -> str:
    return (
        f"min={stats['min']:.6f}, mean={stats['mean']:.6f}, "
        f"p50={stats['p50']:.6f}, p90={stats['p90']:.6f}, "
        f"p99={stats['p99']:.6f}, max={stats['max']:.6f}"
    )


def _format_min_mean_max(stats: dict[str, float]) -> str:
    return f"min={stats['min']:.6f}, mean={stats['mean']:.6f}, max={stats['max']:.6f}"


def _build_section(
    title: str,
    velocities: np.ndarray,
    times: np.ndarray,
    durations: np.ndarray,
    eps: float,
) -> str:
    vel_stats, ratio = _velocity_summary(velocities, eps=eps)
    time_stats = _stats_min_mean_max(times)
    dur_stats = _stats_min_mean_max(durations)
    lines = [
        f"## {title}",
        "",
        f"- `||v||` stats: {_format_stats_row(vel_stats)}",
        f"- `ratio(||v|| < eps)`: {ratio:.6f} (eps={eps:.1e})",
        f"- `times min/mean/max`: {_format_min_mean_max(time_stats)}",
        f"- `durations min/mean/max`: {_format_min_mean_max(dur_stats)}",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Export velocity/timing stats from init NPZ and checkpoint")
    ap.add_argument("--init_npz_path", required=True, help="Path to keyframes_*.npz (step0 source)")
    ap.add_argument("--ckpt_path", required=True, help="Path to ckpt_*.pt (end step source)")
    ap.add_argument("--out_md_path", required=True, help="Output markdown path")
    ap.add_argument("--eps", type=float, default=1e-4, help="Threshold for ratio(||v|| < eps)")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    eps = float(args.eps)
    if eps < 0:
        _fail(f"eps must be >= 0, got {eps}")

    init_npz_path = Path(args.init_npz_path).resolve()
    ckpt_path = Path(args.ckpt_path).resolve()
    out_md_path = Path(args.out_md_path).resolve()

    init_vel, init_times, init_durations = _load_init_npz(init_npz_path)
    ckpt_vel, ckpt_times, ckpt_durations = _load_ckpt(ckpt_path)

    lines = [
        "# Velocity Statistics",
        "",
        f"- init npz: `{init_npz_path}`",
        f"- ckpt: `{ckpt_path}`",
        "",
        _build_section("step0 (init npz)", init_vel, init_times, init_durations, eps=eps).rstrip(),
        "",
        _build_section("step599 (ckpt)", ckpt_vel, ckpt_times, ckpt_durations, eps=eps).rstrip(),
        "",
        "注：checkpoint 中的 `durations` 为 log-duration，本报告已做 `exp()` 还原后再统计。",
        "",
    ]
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[VelocityStats] wrote: {out_md_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"[VelocityStats][ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
