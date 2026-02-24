#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_report_pack.py"


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="report_pack_test_") as td:
        root = Path(td)
        outputs = root / "outputs"
        run_dir = outputs / "gate1_selfcap_demo"  # 用路径名让脚本派生 gate/dataset
        stats_dir = run_dir / "stats"
        stats_dir.mkdir(parents=True, exist_ok=True)
        (stats_dir / "val_step0009.json").write_text(
            json.dumps({"psnr": 1.0, "ssim": 0.2, "lpips": 0.3, "num_GS": 123}),
            encoding="utf-8",
        )

        out_dir = root / "pack"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--outputs_root",
            str(outputs),
            "--out_dir",
            str(out_dir),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"build_report_pack failed:\n{proc.stdout}\n{proc.stderr}")

        csv_path = out_dir / "metrics.csv"
        if not csv_path.exists():
            raise AssertionError("metrics.csv missing")
        text = csv_path.read_text(encoding="utf-8")
        # 期待有派生列（gate/dataset），且 num_GS 能映射到 num_gs
        if "gate" not in text or "dataset" not in text:
            raise AssertionError(f"missing derived columns in csv header: {text.splitlines()[0]}")
        if ",123," not in text:
            raise AssertionError("expected num_gs=123 in csv rows")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: build_report_pack supports args + derived columns")
