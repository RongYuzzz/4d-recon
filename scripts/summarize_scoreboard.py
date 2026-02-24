#!/usr/bin/env python3
"""Summarize report-pack metrics CSV into a markdown scoreboard."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CORE_RUNS = (
    "baseline_600",
    "ours_weak_600",
    "control_weak_nocue_600",
)


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return ROOT / path


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


def _fmt_delta(value: float | None, baseline: float | None) -> str:
    if value is None or baseline is None:
        return "-"
    return f"{(value - baseline):+.4f}"


def _is_strong_variant(run_name: str) -> bool:
    lower = run_name.lower()
    return lower.startswith("ours_strong") and lower.endswith("_600") and "smoke" not in lower


def _is_feature_loss_variant(run_name: str) -> bool:
    lower = run_name.lower()
    return lower.startswith("feature_loss_v1") and "_600" in lower


def _keep_run(run_name: str) -> bool:
    if run_name in CORE_RUNS:
        return True
    return _is_strong_variant(run_name) or _is_feature_loss_variant(run_name)


def _run_order_key(run_name: str) -> tuple[int, str]:
    if run_name == "baseline_600":
        return (0, run_name)
    if run_name == "ours_weak_600":
        return (1, run_name)
    if run_name == "control_weak_nocue_600":
        return (2, run_name)
    if _is_feature_loss_variant(run_name):
        return (3, run_name)
    if _is_strong_variant(run_name):
        return (4, run_name)
    return (5, run_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics_csv", default="outputs/report_pack/metrics.csv")
    parser.add_argument("--out_md", default="outputs/report_pack/scoreboard.md")
    parser.add_argument("--protocol_id", default="")
    parser.add_argument("--select_contains", default="selfcap_bar_8cam60f")
    # Keep default broad enough to include both canonical and /gate1/ symlink paths.
    parser.add_argument("--select_prefix", default="outputs/protocol_v1/")
    parser.add_argument("--step", type=int, default=599)
    parser.add_argument("--stage", default="test")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics_csv = _resolve_path(args.metrics_csv)
    out_md = _resolve_path(args.out_md)

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
            if not _keep_run(run_name):
                continue

            prev = selected.get(run_name)
            if prev is None:
                selected[run_name] = row
                continue

            # Prefer canonical-looking path when multiple rows share same run basename.
            cand = run_dir
            prev_dir = (prev.get("run_dir") or "").strip()
            cand_score = (
                0 if cand.startswith(args.select_prefix) else 1,
                0 if "/gate1/" not in cand else 1,
                len(cand),
                cand,
            )
            prev_score = (
                0 if prev_dir.startswith(args.select_prefix) else 1,
                0 if "/gate1/" not in prev_dir else 1,
                len(prev_dir),
                prev_dir,
            )
            if cand_score < prev_score:
                selected[run_name] = row

    baseline_row = selected.get("baseline_600")
    baseline_psnr = _to_float((baseline_row or {}).get("psnr", ""))
    baseline_ssim = _to_float((baseline_row or {}).get("ssim", ""))
    baseline_lpips = _to_float((baseline_row or {}).get("lpips", ""))
    baseline_tlpips = _to_float((baseline_row or {}).get("tlpips", ""))

    lines: list[str] = []
    lines.append("# Protocol Scoreboard")
    if args.protocol_id:
        lines.append(f"- Protocol: `{args.protocol_id}`")
    lines.append(f"- Source: `{metrics_csv}`")
    lines.append(
        f"- Filter: stage=`{args.stage}`, step=`{args.step}`, contains=`{args.select_contains}`, prefix=`{args.select_prefix}`"
    )
    lines.append("")
    lines.append(
        "| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    for run_name in sorted(selected.keys(), key=_run_order_key):
        row = selected[run_name]
        psnr = _to_float(row.get("psnr", ""))
        ssim = _to_float(row.get("ssim", ""))
        lpips = _to_float(row.get("lpips", ""))
        tlpips = _to_float(row.get("tlpips", ""))
        lines.append(
            "| "
            + " | ".join(
                [
                    run_name,
                    _fmt_metric(psnr),
                    _fmt_metric(ssim),
                    _fmt_metric(lpips),
                    _fmt_metric(tlpips),
                    _fmt_delta(psnr, baseline_psnr),
                    _fmt_delta(ssim, baseline_ssim),
                    _fmt_delta(lpips, baseline_lpips),
                    _fmt_delta(tlpips, baseline_tlpips),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## 结论要点（占位）")
    lines.append("- 结论要点 1：TODO")
    lines.append("- 结论要点 2：TODO")
    lines.append("- 结论要点 3：TODO")
    lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_md} ({len(selected)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
