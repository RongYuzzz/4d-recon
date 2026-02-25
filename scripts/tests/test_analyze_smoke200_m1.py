#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "analyze_smoke200_m1.py"


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
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "10.00",
            "ssim": "0.50",
            "lpips": "0.300",
            "tlpips": "0.030",
            "num_gs": "100",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200_lam0.005",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "10.20",
            "ssim": "0.51",
            "lpips": "0.290",
            "tlpips": "0.026",
            "num_gs": "101",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200_lam0.01",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "10.40",
            "ssim": "0.52",
            "lpips": "0.280",
            "tlpips": "0.027",
            "num_gs": "102",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_gated_smoke200_lam0.005",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "10.10",
            "ssim": "0.505",
            "lpips": "0.295",
            "tlpips": "0.024",
            "num_gs": "103",
            "notes": "",
        },
        # Dominated point: lower PSNR and higher tLPIPS than lam0.005
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200_lam0.02_bad",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "9.90",
            "ssim": "0.49",
            "lpips": "0.310",
            "tlpips": "0.032",
            "num_gs": "104",
            "notes": "",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="analyze_smoke200_m1_", dir=REPO_ROOT) as td:
        root = Path(td)
        metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
        out_md = root / "outputs" / "report_pack" / "scoreboard_smoke200.md"
        _write_metrics_csv(metrics_csv)

        cmd = [
            sys.executable,
            str(SCRIPT),
            "--metrics_csv",
            str(metrics_csv.relative_to(REPO_ROOT)),
            "--out_md",
            str(out_md.relative_to(REPO_ROOT)),
            "--step",
            "199",
            "--stage",
            "test",
            "--select_prefix",
            "outputs/protocol_v1/",
            "--select_contains",
            "selfcap_bar_8cam60f",
            "--baseline_regex",
            "^baseline_smoke200$",
            "--psnr_drop_max",
            "0.5",
            "--tlpips_rise_max",
            "0.01",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            raise RuntimeError(f"analyze_smoke200_m1 failed:\n{proc.stdout}\n{proc.stderr}")
        if not out_md.exists():
            raise AssertionError("scoreboard_smoke200.md missing")

        md = out_md.read_text(encoding="utf-8")
        if "| run | PSNR | tLPIPS | ΔPSNR | ΔLPIPS | ΔtLPIPS |" not in md:
            raise AssertionError("missing M1 table header")
        if "feature_loss_v2_smoke200_lam0.005" not in md:
            raise AssertionError("missing expected run row")
        if "| feature_loss_v2_smoke200_lam0.005 | 10.2000 | 0.0260 | +0.2000 | -0.0100 | -0.0040 |" not in md:
            raise AssertionError("delta row mismatch for lam0.005")

        frontier_section = md.split("## Pareto Frontier", 1)[1]
        if "feature_loss_v2_smoke200_lam0.02_bad" in frontier_section:
            raise AssertionError("dominated point should not appear in pareto frontier")
        for run_name in (
            "feature_loss_v2_smoke200_lam0.005",
            "feature_loss_v2_smoke200_lam0.01",
            "feature_loss_v2_gated_smoke200_lam0.005",
        ):
            if run_name not in frontier_section:
                raise AssertionError(f"missing frontier row: {run_name}")

        rec_section = md.split("## Recommendation", 1)[1]
        if "feature_loss_v2_smoke200_lam0.01" not in rec_section:
            raise AssertionError("best-under-threshold recommendation mismatch")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: analyze_smoke200_m1 outputs table + pareto + recommendation")
