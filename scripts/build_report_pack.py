#!/usr/bin/env python3
"""Build report-pack metrics CSV from validation stats JSON files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STEP_PATTERN = re.compile(r"^val_step(\d+)\.json$")


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return ""


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def _derive_gate(run_dir_display: str) -> str:
    lower = run_dir_display.lower()
    for gate in ("gate0", "gate1", "t0"):
        if gate in lower:
            return gate
    return ""


def _derive_dataset(run_name: str, gate: str) -> str:
    lower = run_name.lower()
    if gate and gate in lower:
        i = lower.find(gate)
        suffix = run_name[i + len(gate) :].lstrip("_-")
        return suffix
    if "_" in run_name:
        return run_name.split("_", 1)[1]
    return ""


def _display_run_dir(run_dir: Path, outputs_root: Path) -> str:
    try:
        return str(run_dir.relative_to(ROOT))
    except ValueError:
        rel_to_outputs = run_dir.relative_to(outputs_root)
        return str(Path(outputs_root.name) / rel_to_outputs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs_root", default="outputs", help="Directory to scan stats from")
    parser.add_argument("--out_dir", default="outputs/report_pack", help="Directory to write metrics.csv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs_root = _resolve_path(args.outputs_root)
    out_dir = _resolve_path(args.out_dir)
    output_csv = out_dir / "metrics.csv"

    stats_files = outputs_root.glob("**/stats/val_step*.json")
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
    for run_dir in sorted(latest_by_run):
        step, stats_path = latest_by_run[run_dir]
        try:
            data = json.loads(stats_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("json root is not an object")
        except Exception as exc:  # pragma: no cover - defensive parsing
            print(f"[warn] skip invalid json: {stats_path} ({exc})", file=sys.stderr)
            continue

        run_dir_display = _display_run_dir(run_dir, outputs_root)
        gate = _derive_gate(run_dir_display)
        dataset = _derive_dataset(run_dir.name, gate)
        rows.append(
            {
                "run_dir": run_dir_display,
                "gate": gate,
                "dataset": dataset,
                "step": step,
                "psnr": _pick(data, "psnr", "PSNR"),
                "ssim": _pick(data, "ssim", "SSIM"),
                "lpips": _pick(data, "lpips", "LPIPS"),
                "num_gs": _pick(data, "num_gs", "num_GS", "numGs"),
                "notes": "",
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_dir",
                "gate",
                "dataset",
                "step",
                "psnr",
                "ssim",
                "lpips",
                "num_gs",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {output_csv} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
