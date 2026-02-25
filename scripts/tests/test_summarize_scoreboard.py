#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "summarize_scoreboard.py"


def _write_metrics_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_dir",
        "gate",
        "dataset",
        "stage",
        "step",
        "psnr",
        "ssim",
        "lpips",
        "tlpips",
        "num_gs",
        "notes",
    ]
    rows = [
        # canonical rows
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600",
            "gate": "",
            "dataset": "600",
            "stage": "test",
            "step": "599",
            "psnr": "10.0",
            "ssim": "0.50",
            "lpips": "0.30",
            "tlpips": "0.020",
            "num_gs": "100",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600",
            "gate": "",
            "dataset": "weak_600",
            "stage": "test",
            "step": "599",
            "psnr": "11.0",
            "ssim": "0.60",
            "lpips": "0.41",
            "tlpips": "0.03",
            "num_gs": "101",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600",
            "gate": "",
            "dataset": "weak_nocue_600",
            "stage": "test",
            "step": "599",
            "psnr": "9.0",
            "ssim": "0.40",
            "lpips": "0.39",
            "tlpips": "0.02",
            "num_gs": "102",
            "notes": "",
        },
        # weak-v2 variants (opt-in only)
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w1.0_end200_600",
            "gate": "",
            "dataset": "weak_v2_600",
            "stage": "test",
            "step": "599",
            "psnr": "10.5",
            "ssim": "0.55",
            "lpips": "0.31",
            "tlpips": "0.021",
            "num_gs": "103",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w1.0_end600_600",
            "gate": "",
            "dataset": "weak_v2_600",
            "stage": "test",
            "step": "599",
            "psnr": "10.4",
            "ssim": "0.54",
            "lpips": "0.32",
            "tlpips": "0.022",
            "num_gs": "104",
            "notes": "",
        },
        # gate1-prefixed strong variants
        {
            "run_dir": "outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_600",
            "gate": "gate1",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "12.0",
            "ssim": "0.65",
            "lpips": "0.20",
            "tlpips": "0.017",
            "num_gs": "105",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_v2_600",
            "gate": "gate1",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "12.5",
            "ssim": "0.66",
            "lpips": "0.19",
            "tlpips": "0.016",
            "num_gs": "106",
            "notes": "",
        },
        # feature-loss variants (should be included)
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "11.7",
            "ssim": "0.62",
            "lpips": "0.24",
            "tlpips": "0.017",
            "num_gs": "107",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_retry_lam0.005_s200_600",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "11.8",
            "ssim": "0.63",
            "lpips": "0.23",
            "tlpips": "0.016",
            "num_gs": "108",
            "notes": "",
        },
        # should be filtered out (smoke)
        {
            "run_dir": "outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_smoke_600",
            "gate": "gate1",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "1.0",
            "ssim": "0.10",
            "lpips": "0.90",
            "tlpips": "0.200",
            "num_gs": "5",
            "notes": "",
        },
        # should be filtered out (wrong stage/step)
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600",
            "gate": "",
            "dataset": "600",
            "stage": "val",
            "step": "599",
            "psnr": "99.0",
            "ssim": "0.99",
            "lpips": "0.01",
            "tlpips": "",
            "num_gs": "100",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600",
            "gate": "",
            "dataset": "weak_600",
            "stage": "test",
            "step": "199",
            "psnr": "50.0",
            "ssim": "0.90",
            "lpips": "0.10",
            "tlpips": "0.005",
            "num_gs": "101",
            "notes": "",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="scoreboard_test_", dir=REPO_ROOT) as td:
        root = Path(td)
        metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
        out_md = root / "outputs" / "report_pack" / "scoreboard.md"
        out_md_with_weak_v2 = root / "outputs" / "report_pack" / "scoreboard_with_weak_v2.md"
        _write_metrics_csv(metrics_csv)
        rel_metrics_csv = metrics_csv.relative_to(REPO_ROOT)
        rel_out_md = out_md.relative_to(REPO_ROOT)
        rel_out_md_with_weak_v2 = out_md_with_weak_v2.relative_to(REPO_ROOT)

        common_cmd = [
            sys.executable,
            str(SCRIPT),
            "--metrics_csv",
            str(rel_metrics_csv),
            "--protocol_id",
            "selfcap_bar_8cam60f_protocol_v1",
            "--select_contains",
            "selfcap_bar_8cam60f",
            "--select_prefix",
            "outputs/protocol_v1/",
            "--step",
            "599",
            "--stage",
            "test",
        ]
        cmd = common_cmd + ["--out_md", str(rel_out_md)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            raise RuntimeError(f"summarize_scoreboard failed:\n{proc.stdout}\n{proc.stderr}")
        if not out_md.exists():
            raise AssertionError("scoreboard.md missing")
        if proc.stdout.strip():
            raise AssertionError(f"stdout should stay empty to avoid redirect corruption, got: {proc.stdout.strip()}")
        if "wrote " not in proc.stderr:
            raise AssertionError("status line should be written to stderr")

        md = out_md.read_text(encoding="utf-8")
        if f"- Source: `{rel_metrics_csv}`" not in md:
            raise AssertionError("repo 内 Source 路径应为相对路径")
        for must in (
            "baseline_600",
            "ours_weak_600",
            "control_weak_nocue_600",
            "ours_strong_600",
            "ours_strong_v2_600",
            "feature_loss_v1_600",
            "feature_loss_v1_retry_lam0.005_s200_600",
        ):
            if must not in md:
                raise AssertionError(f"missing row: {must}")
        for weak_v2 in (
            "ours_weak_v2_w1.0_end200_600",
            "ours_weak_v2_w1.0_end600_600",
        ):
            if weak_v2 in md:
                raise AssertionError("default scoreboard should not include weak_v2 rows")
        if "ours_strong_smoke_600" in md:
            raise AssertionError("smoke row should be filtered out")
        if "ΔPSNR" not in md or "ΔSSIM" not in md or "ΔLPIPS" not in md or "ΔtLPIPS" not in md:
            raise AssertionError("missing delta columns")
        if "| ours_weak_600 | 11.0000 | 0.6000 | 0.4100 | 0.0300 | +1.0000 | +0.1000 | +0.1100 | +0.0100 |" not in md:
            raise AssertionError("unexpected delta row for ours_weak_600")
        if "| control_weak_nocue_600 | 9.0000 | 0.4000 | 0.3900 | 0.0200 | -1.0000 | -0.1000 | +0.0900 | +0.0000 |" not in md:
            raise AssertionError("unexpected row for control_weak_nocue_600")
        if "## 风险提示" not in md:
            raise AssertionError("missing risk section")
        if "control_weak_nocue_600" not in md or "ours_weak_600" not in md:
            raise AssertionError("risk section should mention control vs ours_weak")
        if "结论要点（占位）" not in md:
            raise AssertionError("missing takeaway placeholders")

        cmd_with_weak_v2 = common_cmd + [
            "--out_md",
            str(rel_out_md_with_weak_v2),
            "--include_weak_v2",
        ]
        proc2 = subprocess.run(cmd_with_weak_v2, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc2.returncode != 0:
            raise RuntimeError(f"summarize_scoreboard --include_weak_v2 failed:\n{proc2.stdout}\n{proc2.stderr}")
        if not out_md_with_weak_v2.exists():
            raise AssertionError("scoreboard_with_weak_v2.md missing")
        if proc2.stdout.strip():
            raise AssertionError(
                f"stdout should stay empty with --include_weak_v2, got: {proc2.stdout.strip()}"
            )
        if "wrote " not in proc2.stderr:
            raise AssertionError("status line should be written to stderr with --include_weak_v2")

        md_with_weak_v2 = out_md_with_weak_v2.read_text(encoding="utf-8")
        for weak_v2 in (
            "ours_weak_v2_w1.0_end200_600",
            "ours_weak_v2_w1.0_end600_600",
        ):
            if weak_v2 not in md_with_weak_v2:
                raise AssertionError(f"missing weak_v2 row with flag: {weak_v2}")

    # When metrics path is inside repo, Source should be repo-relative (portable in docs snapshots).
    with tempfile.TemporaryDirectory(prefix="scoreboard_rel_", dir=REPO_ROOT) as td_rel:
        root_rel = Path(td_rel)
        metrics_csv_rel = root_rel / "outputs" / "report_pack" / "metrics.csv"
        out_md_rel = root_rel / "outputs" / "report_pack" / "scoreboard.md"
        _write_metrics_csv(metrics_csv_rel)

        metrics_arg_rel = str(metrics_csv_rel.relative_to(REPO_ROOT))
        out_arg_rel = str(out_md_rel.relative_to(REPO_ROOT))
        cmd_rel = [
            sys.executable,
            str(SCRIPT),
            "--metrics_csv",
            metrics_arg_rel,
            "--out_md",
            out_arg_rel,
            "--select_contains",
            "selfcap_bar_8cam60f",
            "--select_prefix",
            "outputs/protocol_v1/",
            "--step",
            "599",
            "--stage",
            "test",
        ]
        proc_rel = subprocess.run(cmd_rel, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc_rel.returncode != 0:
            raise RuntimeError(f"summarize_scoreboard relative-path run failed:\n{proc_rel.stdout}\n{proc_rel.stderr}")
        md_rel = out_md_rel.read_text(encoding="utf-8")
        expected_source_line = f"- Source: `{metrics_arg_rel}`"
        if expected_source_line not in md_rel:
            raise AssertionError(f"expected repo-relative source line: {expected_source_line}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: summarize_scoreboard supports filtering + strong variants + deltas")
