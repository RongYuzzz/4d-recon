#!/usr/bin/env python3
"""Build report-pack metrics CSV from validation stats JSON files."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CSV = ROOT / "outputs" / "report_pack" / "metrics.csv"
STEP_PATTERN = re.compile(r"^val_step(\d+)\.json$")


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return ""


def main() -> int:
    stats_files = ROOT.glob("outputs/**/stats/val_step*.json")
    latest_by_run: dict[Path, tuple[int, Path]] = {}

    for stats_file in stats_files:
        match = STEP_PATTERN.match(stats_file.name)
        if not match:
            continue
        step = int(match.group(1))
        run_dir = stats_file.parent.parent
        best = latest_by_run.get(run_dir)
        if best is None or step > best[0]:
            latest_by_run[run_dir] = (step, stats_file)

    rows: list[dict[str, Any]] = []
    for run_dir in sorted(latest_by_run, key=lambda p: str(p.relative_to(ROOT))):
        step, stats_path = latest_by_run[run_dir]
        try:
            data = json.loads(stats_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("json root is not an object")
        except Exception as exc:  # pragma: no cover - defensive parsing
            print(f"[warn] skip invalid json: {stats_path} ({exc})", file=sys.stderr)
            continue

        rows.append(
            {
                "run_dir": str(run_dir.relative_to(ROOT)),
                "step": step,
                "psnr": _pick(data, "psnr", "PSNR"),
                "ssim": _pick(data, "ssim", "SSIM"),
                "lpips": _pick(data, "lpips", "LPIPS"),
                "num_gs": _pick(data, "num_gs", "num_GS", "numGs"),
                "notes": "",
            }
        )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["run_dir", "step", "psnr", "ssim", "lpips", "num_gs", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {OUTPUT_CSV} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
