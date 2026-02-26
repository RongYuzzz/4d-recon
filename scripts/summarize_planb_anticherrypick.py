#!/usr/bin/env python3
"""Render fixed Plan-B anti-cherrypick markdown summary from report-pack metrics.csv."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASELINE_PRIORITY = (("baseline_600", "test", 599), ("baseline_smoke200", "test", 199))
PLANB_PRIORITY = (("planb_init_600", "test", 599), ("planb_init_smoke200", "test", 199))


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _to_float(value: str) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _fmt_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def _fmt_delta(planb: float | None, baseline: float | None) -> str:
    if planb is None or baseline is None:
        return "-"
    return f"{(planb - baseline):+.4f}"


def _run_name(run_dir: str) -> str:
    return Path((run_dir or "").rstrip("/")).name


def _filter_group(rows: list[dict[str, str]], group_key: str) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    for row in rows:
        run_dir = (row.get("run_dir") or "").strip()
        if group_key == "canonical":
            if "selfcap_bar_8cam60f/" not in run_dir:
                continue
            if "_seg" in run_dir:
                continue
        elif group_key == "seg200_260":
            if "selfcap_bar_8cam60f_seg200_260" not in run_dir:
                continue
        elif group_key == "seg400_460":
            if "selfcap_bar_8cam60f_seg400_460" not in run_dir:
                continue
        elif group_key == "seg600_660":
            if "selfcap_bar_8cam60f_seg600_660" not in run_dir:
                continue
        elif group_key == "seg300_360":
            if "selfcap_bar_8cam60f_seg300_360" not in run_dir:
                continue
        elif group_key == "seg1800_1860":
            if "selfcap_bar_8cam60f_seg1800_1860" not in run_dir:
                continue
        else:
            continue
        filtered.append(row)
    return filtered


def _pick_row(rows: list[dict[str, str]], priority: tuple[tuple[str, str, int], ...]) -> dict[str, str] | None:
    for run_name, stage, step in priority:
        candidates: list[dict[str, str]] = []
        for row in rows:
            if _run_name(row.get("run_dir", "")) != run_name:
                continue
            if (row.get("stage") or "").strip() != stage:
                continue
            try:
                row_step = int((row.get("step") or "").strip())
            except ValueError:
                continue
            if row_step != step:
                continue
            candidates.append(row)
        if candidates:
            candidates.sort(key=lambda item: (item.get("run_dir") or ""))
            return candidates[0]
    return None


def _line_for_row(row: dict[str, str] | None, fallback_name: str) -> str:
    name = fallback_name
    if row is not None:
        name = _run_name(row.get("run_dir", ""))
    step = (row or {}).get("step", "") or "-"
    psnr = _fmt_metric(_to_float((row or {}).get("psnr", "")))
    lpips = _fmt_metric(_to_float((row or {}).get("lpips", "")))
    tlpips = _fmt_metric(_to_float((row or {}).get("tlpips", "")))
    return f"| {name} | {step} | {psnr} | {lpips} | {tlpips} |"


def _append_group(lines: list[str], title: str, rows: list[dict[str, str]]) -> None:
    baseline_row = _pick_row(rows, BASELINE_PRIORITY)
    planb_row = _pick_row(rows, PLANB_PRIORITY)

    baseline_label = _run_name(baseline_row.get("run_dir", "")) if baseline_row else "baseline (missing)"
    planb_label = _run_name(planb_row.get("run_dir", "")) if planb_row else "planb (missing)"

    baseline_psnr = _to_float((baseline_row or {}).get("psnr", ""))
    baseline_lpips = _to_float((baseline_row or {}).get("lpips", ""))
    baseline_tlpips = _to_float((baseline_row or {}).get("tlpips", ""))
    planb_psnr = _to_float((planb_row or {}).get("psnr", ""))
    planb_lpips = _to_float((planb_row or {}).get("lpips", ""))
    planb_tlpips = _to_float((planb_row or {}).get("tlpips", ""))

    lines.append(f"## {title}")
    lines.append("| run | step | PSNR | LPIPS | tLPIPS |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    lines.append(_line_for_row(baseline_row, baseline_label))
    lines.append(_line_for_row(planb_row, planb_label))
    lines.append(
        "- Delta (planb - baseline): "
        f"ΔPSNR={_fmt_delta(planb_psnr, baseline_psnr)}, "
        f"ΔLPIPS={_fmt_delta(planb_lpips, baseline_lpips)}, "
        f"ΔtLPIPS={_fmt_delta(planb_tlpips, baseline_tlpips)}"
    )
    lines.append("")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics_csv", default="outputs/report_pack/metrics.csv")
    parser.add_argument("--out_md", default="outputs/report_pack/planb_anticherrypick.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics_csv = _resolve_path(args.metrics_csv)
    out_md = _resolve_path(args.out_md)

    if not metrics_csv.exists():
        raise FileNotFoundError(f"metrics csv missing: {metrics_csv}")

    with metrics_csv.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    lines: list[str] = []
    lines.append("# Plan-B Anti-Cherrypick Summary")
    lines.append(f"- Source: `{_display_path(metrics_csv)}`")
    lines.append("")

    _append_group(lines, "Canonical", _filter_group(rows, "canonical"))
    _append_group(lines, "seg200_260", _filter_group(rows, "seg200_260"))
    _append_group(lines, "seg400_460", _filter_group(rows, "seg400_460"))

    seg600_rows = _filter_group(rows, "seg600_660")
    seg300_rows = _filter_group(rows, "seg300_360")
    if seg600_rows:
        _append_group(lines, "seg600_660", seg600_rows)
    elif seg300_rows:
        _append_group(lines, "seg300_360 (fallback)", seg300_rows)
    else:
        _append_group(lines, "seg600_660 (missing)", [])

    seg1800_rows = _filter_group(rows, "seg1800_1860")
    if seg1800_rows:
        _append_group(lines, "seg1800_1860", seg1800_rows)
    else:
        _append_group(lines, "seg1800_1860 (missing)", [])

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_md}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
