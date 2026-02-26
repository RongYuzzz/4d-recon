#!/usr/bin/env python3
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "summarize_planb_anticherrypick.py"


def _section_text(md: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = md.find(marker)
    if start < 0:
        raise AssertionError(f"missing heading: {heading}")
    end = md.find("\n## ", start + len(marker))
    if end < 0:
        end = len(md)
    return md[start:end]


def _render_markdown(rows: list[dict[str, str]], root: Path) -> str:
    metrics_csv = root / "outputs" / "report_pack" / "metrics.csv"
    out_md = root / "outputs" / "report_pack" / "planb_anticherrypick.md"
    metrics_csv.parent.mkdir(parents=True, exist_ok=True)

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
    with metrics_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    cmd = [
        sys.executable,
        str(SCRIPT),
        "--metrics_csv",
        str(metrics_csv.relative_to(REPO_ROOT)),
        "--out_md",
        str(out_md.relative_to(REPO_ROOT)),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if proc.returncode != 0:
        raise RuntimeError(
            "summarize_planb_anticherrypick failed:\n"
            f"{proc.stdout}\n{proc.stderr}"
        )
    if not out_md.exists():
        raise AssertionError("planb_anticherrypick markdown missing")
    return out_md.read_text(encoding="utf-8")


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="planb_anticherry_", dir=REPO_ROOT) as td:
        root = Path(td)
        common_rows = [
            {
                "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f",
                "stage": "test",
                "step": "599",
                "psnr": "10.0",
                "ssim": "0.50",
                "lpips": "0.300",
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
                "psnr": "10.6",
                "ssim": "0.55",
                "lpips": "0.270",
                "tlpips": "0.018",
                "num_gs": "110",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f_seg200_260/baseline_600",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg200_260",
                "stage": "test",
                "step": "599",
                "psnr": "9.2",
                "ssim": "0.42",
                "lpips": "0.350",
                "tlpips": "0.025",
                "num_gs": "95",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f_seg200_260/planb_init_600",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg200_260",
                "stage": "test",
                "step": "599",
                "psnr": "9.8",
                "ssim": "0.47",
                "lpips": "0.310",
                "tlpips": "0.022",
                "num_gs": "103",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f_seg400_460/baseline_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg400_460",
                "stage": "test",
                "step": "199",
                "psnr": "8.7",
                "ssim": "0.38",
                "lpips": "0.390",
                "tlpips": "0.032",
                "num_gs": "90",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg400_460",
                "stage": "test",
                "step": "199",
                "psnr": "9.1",
                "ssim": "0.41",
                "lpips": "0.360",
                "tlpips": "0.028",
                "num_gs": "96",
                "notes": "",
            },
        ]
        seg600_rows = [
            {
                "run_dir": "outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/baseline_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg600_660",
                "stage": "test",
                "step": "199",
                "psnr": "8.9",
                "ssim": "0.39",
                "lpips": "0.400",
                "tlpips": "0.033",
                "num_gs": "90",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/planb_init_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg600_660",
                "stage": "test",
                "step": "199",
                "psnr": "9.3",
                "ssim": "0.42",
                "lpips": "0.370",
                "tlpips": "0.029",
                "num_gs": "96",
                "notes": "",
            },
        ]
        seg1800_rows = [
            {
                "run_dir": "outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg1800_1860",
                "stage": "test",
                "step": "199",
                "psnr": "8.95",
                "ssim": "0.39",
                "lpips": "0.398",
                "tlpips": "0.034",
                "num_gs": "90",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg1800_1860",
                "stage": "test",
                "step": "199",
                "psnr": "9.28",
                "ssim": "0.42",
                "lpips": "0.372",
                "tlpips": "0.030",
                "num_gs": "96",
                "notes": "",
            },
        ]

        seg300_rows = [
            {
                "run_dir": "outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg300_360",
                "stage": "test",
                "step": "199",
                "psnr": "8.8",
                "ssim": "0.39",
                "lpips": "0.401",
                "tlpips": "0.034",
                "num_gs": "90",
                "notes": "",
            },
            {
                "run_dir": "outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200",
                "gate": "",
                "dataset": "selfcap_bar_8cam60f_seg300_360",
                "stage": "test",
                "step": "199",
                "psnr": "9.0",
                "ssim": "0.40",
                "lpips": "0.390",
                "tlpips": "0.031",
                "num_gs": "95",
                "notes": "",
            },
        ]

        md = _render_markdown(common_rows + seg600_rows + seg300_rows + seg1800_rows, root)
        for heading in ("Canonical", "seg200_260", "seg400_460", "seg600_660", "seg300_360", "seg1800_1860"):
            section = _section_text(md, heading)
            for token in ("ΔPSNR", "ΔLPIPS", "ΔtLPIPS"):
                if token not in section:
                    raise AssertionError(f"missing token {token} in section {heading}")

        md_fallback = _render_markdown(common_rows + seg300_rows, root)
        missing_seg600 = _section_text(md_fallback, "seg600_660 (missing)")
        if "ΔPSNR=-" not in missing_seg600:
            raise AssertionError("missing seg600 section should render dash deltas")
        section = _section_text(md_fallback, "seg300_360")
        for token in ("ΔPSNR", "ΔLPIPS", "ΔtLPIPS"):
            if token not in section:
                raise AssertionError(f"missing token {token} in seg300 section")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: summarize_planb_anticherrypick renders seg sections with deltas and seg300 companion slot")
