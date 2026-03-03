#!/usr/bin/env python3
"""Summarize report-pack metrics CSV into a markdown scoreboard."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CORE_RUNS = (
    "baseline_600",
    "ours_weak_600",
    "control_weak_nocue_600",
    "planb_init_600",
)


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


def _fmt_delta(value: float | None, baseline: float | None) -> str:
    if value is None or baseline is None:
        return "-"
    return f"{(value - baseline):+.4f}"


def _is_strong_variant(run_name: str) -> bool:
    lower = run_name.lower()
    return lower.startswith("ours_strong") and lower.endswith("_600") and "smoke" not in lower


def _is_feature_loss_variant(run_name: str) -> bool:
    lower = run_name.lower()
    if "smoke" in lower:
        return False
    if not lower.endswith("_600"):
        return False
    return lower.startswith("feature_loss_v1") or lower.startswith("feature_loss_v2")


def _is_planb_feat_v2_variant(run_name: str) -> bool:
    lower = run_name.lower()
    return lower.startswith("planb_feat_v2_") or lower.startswith("planb_feature_loss_v2_")


def _is_weak_v2_variant(run_name: str) -> bool:
    lower = run_name.lower()
    return lower.startswith("ours_weak_v2_") and lower.endswith("_600")


def _is_planb_variant(run_name: str) -> bool:
    lower = run_name.lower()
    if "smoke" in lower:
        return False
    return lower.startswith("planb_") and lower.endswith("_600")


def _keep_run(run_name: str, include_weak_v2: bool) -> bool:
    if run_name in CORE_RUNS:
        return True
    if _is_planb_variant(run_name):
        return True
    if _is_planb_feat_v2_variant(run_name):
        return True
    if include_weak_v2 and _is_weak_v2_variant(run_name):
        return True
    return _is_strong_variant(run_name) or _is_feature_loss_variant(run_name)


def _run_order_key(run_name: str) -> tuple[int, str]:
    if run_name == "baseline_600":
        return (0, run_name)
    if run_name == "ours_weak_600":
        return (1, run_name)
    if _is_weak_v2_variant(run_name):
        return (2, run_name)
    if run_name == "control_weak_nocue_600":
        return (3, run_name)
    if _is_planb_variant(run_name):
        return (4, run_name)
    if _is_planb_feat_v2_variant(run_name):
        return (5, run_name)
    if _is_feature_loss_variant(run_name):
        return (6, run_name)
    if _is_strong_variant(run_name):
        return (7, run_name)
    return (7, run_name)


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
    parser.add_argument(
        "--delta_baseline_run",
        default="",
        help="If set, compute deltas against this run basename (searched across all prefixes).",
    )
    parser.add_argument("--include_weak_v2", action="store_true")
    return parser.parse_args()


def _pick_preferred_row(run_dir: str, prev_dir: str, preferred_prefix: str) -> bool:
    """Return True if run_dir should replace prev_dir as the preferred choice."""
    cand_score = (
        0 if (preferred_prefix and run_dir.startswith(preferred_prefix)) else 1,
        0 if "/gate1/" not in run_dir else 1,
        len(run_dir),
        run_dir,
    )
    prev_score = (
        0 if (preferred_prefix and prev_dir.startswith(preferred_prefix)) else 1,
        0 if "/gate1/" not in prev_dir else 1,
        len(prev_dir),
        prev_dir,
    )
    return cand_score < prev_score


def main() -> int:
    args = parse_args()
    metrics_csv = _resolve_path(args.metrics_csv)
    out_md = _resolve_path(args.out_md)

    if not metrics_csv.exists():
        raise FileNotFoundError(f"metrics csv missing: {metrics_csv}")

    selected: dict[str, dict[str, str]] = {}
    delta_baseline_row: dict[str, str] | None = None
    with metrics_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_dir = (row.get("run_dir") or "").strip()
            if args.select_contains and args.select_contains not in run_dir:
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

            if args.delta_baseline_run and run_name == args.delta_baseline_run:
                prev = delta_baseline_row
                if prev is None:
                    delta_baseline_row = row
                else:
                    prev_dir = (prev.get("run_dir") or "").strip()
                    if _pick_preferred_row(run_dir, prev_dir, args.select_prefix):
                        delta_baseline_row = row

            if args.select_prefix and not run_dir.startswith(args.select_prefix):
                continue
            if not _keep_run(run_name, args.include_weak_v2):
                continue

            prev = selected.get(run_name)
            if prev is None:
                selected[run_name] = row
                continue

            # Prefer canonical-looking path when multiple rows share same run basename.
            cand = run_dir
            prev_dir = (prev.get("run_dir") or "").strip()
            if _pick_preferred_row(cand, prev_dir, args.select_prefix):
                selected[run_name] = row

    baseline_row = selected.get("baseline_600")
    delta_row = delta_baseline_row if args.delta_baseline_run else baseline_row
    baseline_psnr = _to_float((delta_row or {}).get("psnr", ""))
    baseline_ssim = _to_float((delta_row or {}).get("ssim", ""))
    baseline_lpips = _to_float((delta_row or {}).get("lpips", ""))
    baseline_tlpips = _to_float((delta_row or {}).get("tlpips", ""))

    lines: list[str] = []
    lines.append("# Protocol Scoreboard")
    if args.protocol_id:
        lines.append(f"- Protocol: `{args.protocol_id}`")
    lines.append(f"- Source: `{_display_path(metrics_csv)}`")
    lines.append(
        f"- Filter: stage=`{args.stage}`, step=`{args.step}`, contains=`{args.select_contains}`, prefix=`{args.select_prefix}`"
    )
    if args.delta_baseline_run:
        lines.append(f"- Delta baseline: `{args.delta_baseline_run}`")
        if delta_row is None:
            lines.append("- Delta baseline status: <missing in metrics.csv for this filter>")
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
    lines.append("## 风险提示")
    risk_lines: list[str] = []
    risk_summary = "无法判断：缺少风险对照结论。"
    control = selected.get("control_weak_nocue_600")
    ours_weak = selected.get("ours_weak_600")
    missing_core: list[str] = []
    if not ours_weak:
        missing_core.append("ours_weak_600")
    if not control:
        missing_core.append("control_weak_nocue_600")

    if missing_core:
        missing_fmt = "、".join(f"`{name}`" for name in missing_core)
        message = f"无法判断：缺少 {missing_fmt}。"
        lines.append(f"- {message}")
        risk_summary = message
    else:
        control_tlpips = _to_float(control.get("tlpips", ""))
        ours_tlpips = _to_float(ours_weak.get("tlpips", ""))
        control_lpips = _to_float(control.get("lpips", ""))
        ours_lpips = _to_float(ours_weak.get("lpips", ""))
        control_psnr = _to_float(control.get("psnr", ""))
        ours_psnr = _to_float(ours_weak.get("psnr", ""))
        control_ssim = _to_float(control.get("ssim", ""))
        ours_ssim = _to_float(ours_weak.get("ssim", ""))

        comparable = False
        # Risk should trigger when control performs better than ours_weak.
        if control_tlpips is not None and ours_tlpips is not None:
            comparable = True
            if control_tlpips < ours_tlpips:
                risk_lines.append(
                    "- <span style='color:red'>`control_weak_nocue_600` 的 tLPIPS 优于 `ours_weak_600`，提示当前 cue/注入方式可能产生负增益。</span>"
                )
        if not risk_lines and control_lpips is not None and ours_lpips is not None:
            comparable = True
            if control_lpips < ours_lpips:
                risk_lines.append(
                    "- <span style='color:red'>`control_weak_nocue_600` 的 LPIPS 优于 `ours_weak_600`，提示当前 cue/注入方式可能产生负增益。</span>"
                )
        if not risk_lines and control_psnr is not None and ours_psnr is not None:
            comparable = True
            if control_psnr > ours_psnr:
                risk_lines.append(
                    "- <span style='color:red'>`control_weak_nocue_600` 的 PSNR 优于 `ours_weak_600`，提示当前 cue/注入方式可能产生负增益。</span>"
                )
        if not risk_lines and control_ssim is not None and ours_ssim is not None:
            comparable = True
            if control_ssim > ours_ssim:
                risk_lines.append(
                    "- <span style='color:red'>`control_weak_nocue_600` 的 SSIM 优于 `ours_weak_600`，提示当前 cue/注入方式可能产生负增益。</span>"
                )

        if risk_lines:
            lines.extend(risk_lines)
            risk_summary = "发现 `control_weak_nocue_600` 相对 `ours_weak_600` 的潜在负增益风险。"
        elif comparable:
            message = "未发现 `control_weak_nocue_600` 优于 `ours_weak_600` 的风险信号。"
            lines.append(f"- {message}")
            risk_summary = message
        else:
            message = "无法判断：`control_weak_nocue_600` 与 `ours_weak_600` 缺少可比指标（tLPIPS/LPIPS/PSNR/SSIM）。"
            lines.append(f"- {message}")
            risk_summary = message

    best_psnr: tuple[str, float] | None = None
    best_tlpips: tuple[str, float] | None = None
    for run_name, row in selected.items():
        psnr = _to_float(row.get("psnr", ""))
        if psnr is not None:
            if best_psnr is None or psnr > best_psnr[1] or (psnr == best_psnr[1] and run_name < best_psnr[0]):
                best_psnr = (run_name, psnr)
        tlpips = _to_float(row.get("tlpips", ""))
        if tlpips is not None:
            if (
                best_tlpips is None
                or tlpips < best_tlpips[1]
                or (tlpips == best_tlpips[1] and run_name < best_tlpips[0])
            ):
                best_tlpips = (run_name, tlpips)

    lines.append("")
    lines.append("## 结论要点（自动生成）")
    if best_psnr is None:
        lines.append("- PSNR 最优：无法判断（缺少可用 PSNR）。")
    else:
        lines.append(f"- PSNR 最优：`{best_psnr[0]}` ({best_psnr[1]:.4f})")
    if best_tlpips is None:
        lines.append("- tLPIPS 最优：无法判断（缺少可用 tLPIPS）。")
    else:
        lines.append(f"- tLPIPS 最优：`{best_tlpips[0]}` ({best_tlpips[1]:.4f})")
    lines.append(f"- 风险提示：{risk_summary}")
    lines.append("")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_md} ({len(selected)} runs)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
