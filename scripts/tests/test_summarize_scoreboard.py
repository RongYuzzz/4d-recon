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
            "lpips": "0.25",
            "tlpips": "0.018",
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
            "lpips": "0.35",
            "tlpips": "",
            "num_gs": "102",
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
            "num_gs": "103",
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
            "num_gs": "104",
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
    with tempfile.TemporaryDirectory(prefix="scoreboard_test_") as td:
        root = Path(td)
        metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
        out_md = root / "outputs" / "report_pack" / "scoreboard.md"
        _write_metrics_csv(metrics_csv)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--metrics_csv",
            str(metrics_csv),
            "--out_md",
            str(out_md),
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
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"summarize_scoreboard failed:\n{proc.stdout}\n{proc.stderr}")
        if not out_md.exists():
            raise AssertionError("scoreboard.md missing")

        md = out_md.read_text(encoding="utf-8")
        for must in (
            "baseline_600",
            "ours_weak_600",
            "control_weak_nocue_600",
            "ours_strong_600",
            "ours_strong_v2_600",
        ):
            if must not in md:
                raise AssertionError(f"missing row: {must}")
        if "ours_strong_smoke_600" in md:
            raise AssertionError("smoke row should be filtered out")
        if "ΔPSNR" not in md or "ΔSSIM" not in md or "ΔLPIPS" not in md or "ΔtLPIPS" not in md:
            raise AssertionError("missing delta columns")
        if "| ours_weak_600 | 11.0000 | 0.6000 | 0.2500 | 0.0180 | +1.0000 | +0.1000 | -0.0500 | -0.0020 |" not in md:
            raise AssertionError("unexpected delta row for ours_weak_600")
        if "| control_weak_nocue_600 | 9.0000 | 0.4000 | 0.3500 | - | -1.0000 | -0.1000 | +0.0500 | - |" not in md:
            raise AssertionError("empty tlpips should be rendered as '-'")
        if "结论要点（占位）" not in md:
            raise AssertionError("missing takeaway placeholders")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: summarize_scoreboard supports filtering + strong variants + deltas")
