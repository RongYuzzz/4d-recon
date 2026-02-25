#!/usr/bin/env python3
"""Analyze smoke200 M1 metrics: scoreboard deltas, Pareto frontier, recommendation."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@dataclass
class RunRow:
    run_name: str
    run_dir: str
    psnr: float
    lpips: float
    tlpips: float


def _resolve_path(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return ROOT / p


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _to_float_or_raise(text: str, field_name: str, run_name: str) -> float:
    s = (text or "").strip()
    if not s:
        raise ValueError(f"missing {field_name} for run {run_name}")
    try:
        return float(s)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name} for run {run_name}: {s!r}") from exc


def _fmt(v: float) -> str:
    return f"{v:.4f}"


def _fmt_delta(v: float, base: float) -> str:
    return f"{(v - base):+.4f}"


def _choose_preferred(prev_dir: str, cand_dir: str, prefix: str) -> bool:
    prev_score = (
        0 if prev_dir.startswith(prefix) else 1,
        0 if "/gate1/" not in prev_dir else 1,
        len(prev_dir),
        prev_dir,
    )
    cand_score = (
        0 if cand_dir.startswith(prefix) else 1,
        0 if "/gate1/" not in cand_dir else 1,
        len(cand_dir),
        cand_dir,
    )
    return cand_score < prev_score


def _is_dominated(target: RunRow, others: list[RunRow]) -> bool:
    for row in others:
        if row.run_name == target.run_name:
            continue
        better_or_equal_psnr = row.psnr >= target.psnr
        better_or_equal_tlpips = row.tlpips <= target.tlpips
        strictly_better = row.psnr > target.psnr or row.tlpips < target.tlpips
        if better_or_equal_psnr and better_or_equal_tlpips and strictly_better:
            return True
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics_csv", default="outputs/report_pack/metrics.csv")
    parser.add_argument("--out_md", default="outputs/report_pack/scoreboard_smoke200.md")
    parser.add_argument("--step", type=int, default=199)
    parser.add_argument("--stage", default="test")
    parser.add_argument("--select_prefix", default="outputs/protocol_v1/")
    parser.add_argument("--select_contains", default="selfcap_bar_8cam60f")
    parser.add_argument("--baseline_regex", default=r"^baseline_smoke200")
    parser.add_argument("--psnr_drop_max", type=float, default=0.5)
    parser.add_argument("--tlpips_rise_max", type=float, default=0.01)
    parser.add_argument("--emit_json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics_csv = _resolve_path(args.metrics_csv)
    out_md = _resolve_path(args.out_md)
    baseline_re = re.compile(args.baseline_regex)

    if not metrics_csv.exists():
        raise FileNotFoundError(f"metrics csv missing: {metrics_csv}")

    selected: dict[str, dict[str, str]] = {}
    with metrics_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_dir = (row.get("run_dir") or "").strip()
            if args.select_contains and args.select_contains not in run_dir:
                continue
            if args.select_prefix and not run_dir.startswith(args.select_prefix):
                continue
            if (row.get("stage") or "").strip() != args.stage:
                continue
            try:
                step = int((row.get("step") or "").strip())
            except ValueError:
                continue
            if step != args.step:
                continue
            run_name = Path(run_dir.rstrip("/")).name
            prev = selected.get(run_name)
            if prev is None:
                selected[run_name] = row
            else:
                prev_dir = (prev.get("run_dir") or "").strip()
                if _choose_preferred(prev_dir, run_dir, args.select_prefix):
                    selected[run_name] = row

    rows: list[RunRow] = []
    for run_name in sorted(selected.keys()):
        row = selected[run_name]
        rows.append(
            RunRow(
                run_name=run_name,
                run_dir=(row.get("run_dir") or "").strip(),
                psnr=_to_float_or_raise(row.get("psnr", ""), "psnr", run_name),
                lpips=_to_float_or_raise(row.get("lpips", ""), "lpips", run_name),
                tlpips=_to_float_or_raise(row.get("tlpips", ""), "tlpips", run_name),
            )
        )
    if not rows:
        raise RuntimeError("no runs selected after filtering")

    baseline_candidates = [r for r in rows if baseline_re.search(r.run_name)]
    if not baseline_candidates:
        raise RuntimeError(f"no baseline matched regex: {args.baseline_regex}")
    baseline = sorted(baseline_candidates, key=lambda x: x.run_name)[0]

    frontier = [r for r in rows if not _is_dominated(r, rows)]
    frontier = sorted(frontier, key=lambda x: (-x.psnr, x.tlpips, x.run_name))

    feasible = [
        r
        for r in rows
        if r.psnr >= baseline.psnr - float(args.psnr_drop_max)
        and r.tlpips <= baseline.tlpips + float(args.tlpips_rise_max)
    ]
    recommendation: RunRow | None = None
    if feasible:
        recommendation = sorted(feasible, key=lambda x: (-x.psnr, x.tlpips, x.run_name))[0]

    lines: list[str] = []
    lines.append("# Smoke200 M1 Analysis")
    lines.append(f"- Source: `{_display_path(metrics_csv)}`")
    lines.append(
        f"- Filter: stage=`{args.stage}`, step=`{args.step}`, contains=`{args.select_contains}`, prefix=`{args.select_prefix}`"
    )
    lines.append(f"- Baseline: `{baseline.run_name}`")
    lines.append("")
    lines.append("## M1 Table")
    lines.append("| run | PSNR | tLPIPS | ΔPSNR | ΔLPIPS | ΔtLPIPS |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    r.run_name,
                    _fmt(r.psnr),
                    _fmt(r.tlpips),
                    _fmt_delta(r.psnr, baseline.psnr),
                    _fmt_delta(r.lpips, baseline.lpips),
                    _fmt_delta(r.tlpips, baseline.tlpips),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Pareto Frontier")
    lines.append("| run | PSNR | tLPIPS |")
    lines.append("| --- | ---: | ---: |")
    for r in frontier:
        lines.append(f"| {r.run_name} | {_fmt(r.psnr)} | {_fmt(r.tlpips)} |")
    lines.append("")
    lines.append("## Recommendation")
    if recommendation is None:
        lines.append(
            "- 未找到满足阈值约束的 run。"
            f"约束：PSNR >= baseline - {args.psnr_drop_max}, "
            f"tLPIPS <= baseline + {args.tlpips_rise_max}。"
        )
    else:
        lines.append(
            "- 推荐 run："
            f"`{recommendation.run_name}` "
            f"(PSNR={_fmt(recommendation.psnr)}, tLPIPS={_fmt(recommendation.tlpips)})"
        )
        lines.append(
            f"- 约束：PSNR >= {baseline.psnr - float(args.psnr_drop_max):.4f}, "
            f"tLPIPS <= {baseline.tlpips + float(args.tlpips_rise_max):.4f}"
        )
    lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")

    if args.emit_json:
        payload = {
            "baseline": baseline.__dict__,
            "rows": [r.__dict__ for r in rows],
            "pareto_frontier": [r.__dict__ for r in frontier],
            "recommendation": recommendation.__dict__ if recommendation else None,
        }
        out_json = out_md.with_suffix(".json")
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_md} and {out_json}", file=sys.stderr)
    else:
        print(f"wrote {out_md}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
