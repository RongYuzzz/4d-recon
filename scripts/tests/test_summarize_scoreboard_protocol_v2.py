from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
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
        # protocol_v1 baselines
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
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
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "11.2",
            "ssim": "0.61",
            "lpips": "0.28",
            "tlpips": "0.019",
            "num_gs": "111",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "11.5",
            "ssim": "0.60",
            "lpips": "0.29",
            "tlpips": "0.025",
            "num_gs": "112",
            "notes": "",
        },
        # protocol_v2 (stage-2) runs
        {
            "run_dir": "outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "199",
            "psnr": "12.0",
            "ssim": "0.62",
            "lpips": "0.27",
            "tlpips": "0.020",
            "num_gs": "120",
            "notes": "",
        },
        {
            "run_dir": "outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400",
            "gate": "",
            "dataset": "selfcap_bar_8cam60f",
            "stage": "test",
            "step": "599",
            "psnr": "10.8",
            "ssim": "0.58",
            "lpips": "0.29",
            "tlpips": "0.021",
            "num_gs": "121",
            "notes": "",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class SummarizeScoreboardProtocolV2Tests(unittest.TestCase):
    def test_v2_only_smoke200_should_include_planb_feat_v2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scoreboard_v2_smoke_", dir=REPO_ROOT) as td:
            root = Path(td)
            metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
            out_md = root / "outputs" / "report_pack" / "scoreboard_v2_smoke200.md"
            _write_metrics_csv(metrics_csv)

            cmd = [
                sys.executable,
                str(SCRIPT),
                "--metrics_csv",
                str(metrics_csv.relative_to(REPO_ROOT)),
                "--out_md",
                str(out_md.relative_to(REPO_ROOT)),
                "--select_contains",
                "selfcap_bar_8cam60f",
                "--select_prefix",
                "outputs/protocol_v2/",
                "--step",
                "199",
                "--stage",
                "test",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")
            md = out_md.read_text(encoding="utf-8")
            self.assertIn("planb_feat_v2_smoke200_lam0.005_warm100", md)

    def test_smoke200_delta_baseline_can_use_planb_init_smoke200(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scoreboard_v2_smoke_delta_", dir=REPO_ROOT) as td:
            root = Path(td)
            metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
            out_md = root / "outputs" / "report_pack" / "scoreboard_v2_smoke200_delta.md"
            _write_metrics_csv(metrics_csv)

            cmd = [
                sys.executable,
                str(SCRIPT),
                "--metrics_csv",
                str(metrics_csv.relative_to(REPO_ROOT)),
                "--out_md",
                str(out_md.relative_to(REPO_ROOT)),
                "--select_contains",
                "selfcap_bar_8cam60f",
                "--select_prefix",
                "outputs/protocol_v2/",
                "--step",
                "199",
                "--stage",
                "test",
                "--delta_baseline_run",
                "planb_init_smoke200",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")
            md = out_md.read_text(encoding="utf-8")
            self.assertIn("- Delta baseline: `planb_init_smoke200`", md)
            self.assertIn("| planb_feat_v2_smoke200_lam0.005_warm100 |", md)
            self.assertNotIn("| - | - | - | - |", md)
            self.assertIn("+0.5000", md)  # ΔPSNR: 12.0 - 11.5
            self.assertIn("-0.0050", md)  # ΔtLPIPS: 0.020 - 0.025

    def test_v2_only_full600_should_include_planb_feat_v2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scoreboard_v2_full_", dir=REPO_ROOT) as td:
            root = Path(td)
            metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
            out_md = root / "outputs" / "report_pack" / "scoreboard_v2_full600.md"
            _write_metrics_csv(metrics_csv)

            cmd = [
                sys.executable,
                str(SCRIPT),
                "--metrics_csv",
                str(metrics_csv.relative_to(REPO_ROOT)),
                "--out_md",
                str(out_md.relative_to(REPO_ROOT)),
                "--select_contains",
                "selfcap_bar_8cam60f",
                "--select_prefix",
                "outputs/protocol_v2/",
                "--step",
                "599",
                "--stage",
                "test",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")
            md = out_md.read_text(encoding="utf-8")
            self.assertIn("planb_feat_v2_full600_lam0.005_warm100_ramp400", md)

    def test_cross_protocol_full600_should_include_v1_and_v2_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="scoreboard_cross_", dir=REPO_ROOT) as td:
            root = Path(td)
            metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
            out_md = root / "outputs" / "report_pack" / "scoreboard_full600_vs_v1.md"
            _write_metrics_csv(metrics_csv)

            cmd = [
                sys.executable,
                str(SCRIPT),
                "--metrics_csv",
                str(metrics_csv.relative_to(REPO_ROOT)),
                "--out_md",
                str(out_md.relative_to(REPO_ROOT)),
                "--select_contains",
                "selfcap_bar_8cam60f",
                "--select_prefix",
                "",
                "--step",
                "599",
                "--stage",
                "test",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")
            md = out_md.read_text(encoding="utf-8")
            for must in (
                "baseline_600",
                "planb_init_600",
                "planb_feat_v2_full600_lam0.005_warm100_ramp400",
            ):
                self.assertIn(must, md)


if __name__ == "__main__":
    unittest.main()
