#!/usr/bin/env python3
"""Plot PSNR and tLPIPS vs step for convergecheck (baseline vs planb_init)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Point:
    step: int
    psnr: float
    tlpips: float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline_dir", required=True, help="Run directory (contains stats/test_step*.json)")
    p.add_argument("--planb_dir", required=True, help="Run directory (contains stats/test_step*.json)")
    p.add_argument("--out_png", required=True, help="Output PNG path")
    return p.parse_args()


def _load_points(run_dir: Path) -> list[Point]:
    stats_dir = run_dir / "stats"
    if not stats_dir.exists():
        raise FileNotFoundError(f"missing stats dir: {stats_dir}")

    points: list[Point] = []
    for p in sorted(stats_dir.glob("test_step*.json")):
        step_str = p.stem.split("test_step", 1)[-1]
        if not step_str.isdigit():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        points.append(
            Point(
                step=int(step_str),
                psnr=float(data["psnr"]),
                tlpips=float(data["tlpips"]),
            )
        )
    if not points:
        raise RuntimeError(f"no test_step*.json found in {stats_dir}")
    return points


def main() -> int:
    args = parse_args()
    baseline_dir = Path(args.baseline_dir)
    planb_dir = Path(args.planb_dir)
    out_png = Path(args.out_png)

    baseline = _load_points(baseline_dir)
    planb = _load_points(planb_dir)

    import matplotlib.pyplot as plt

    fig, (ax_psnr, ax_tlpips) = plt.subplots(2, 1, figsize=(8, 6), sharex=True, constrained_layout=True)

    ax_psnr.plot([p.step for p in baseline], [p.psnr for p in baseline], marker="o", label="baseline")
    ax_psnr.plot([p.step for p in planb], [p.psnr for p in planb], marker="o", label="planb_init")
    ax_psnr.set_ylabel("PSNR ↑")
    ax_psnr.grid(True, alpha=0.3)
    ax_psnr.legend(loc="lower right")

    ax_tlpips.plot([p.step for p in baseline], [p.tlpips for p in baseline], marker="o", label="baseline")
    ax_tlpips.plot([p.step for p in planb], [p.tlpips for p in planb], marker="o", label="planb_init")
    ax_tlpips.set_xlabel("Step")
    ax_tlpips.set_ylabel("tLPIPS ↓")
    ax_tlpips.grid(True, alpha=0.3)

    last_b = baseline[-1]
    last_p = planb[-1]
    title = (
        "Convergecheck (dur0, L4D=1e-4)\n"
        f"Final ΔPSNR={last_p.psnr - last_b.psnr:+.3f}, ΔtLPIPS={last_p.tlpips - last_b.tlpips:+.4f} (planb - baseline)"
    )
    fig.suptitle(title)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200)
    print(f"wrote {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

