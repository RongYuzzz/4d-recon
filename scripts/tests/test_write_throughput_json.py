#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "write_throughput_json.py"


def run_test() -> None:
    with tempfile.TemporaryDirectory(prefix="throughput_json_test_") as td:
        root = Path(td)
        result_dir = root / "outputs" / "protocol_v1" / "selfcap_bar_8cam60f" / "baseline_smoke200"
        stats_dir = result_dir / "stats"
        stats_dir.mkdir(parents=True, exist_ok=True)

        (stats_dir / "train_step0199.json").write_text(
            json.dumps({"ellipse_time": 100.0, "num_GS": 12345}),
            encoding="utf-8",
        )

        cmd = [sys.executable, str(SCRIPT), str(result_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            raise AssertionError(
                "write_throughput_json failed\n"
                f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
            )

        out_path = stats_dir / "throughput.json"
        if not out_path.exists():
            raise AssertionError(f"missing throughput file: {out_path}")

        obj = json.loads(out_path.read_text(encoding="utf-8"))
        for key in ("source_stats", "step", "elapsed_sec", "iter_per_sec"):
            if key not in obj:
                raise AssertionError(f"missing key in throughput.json: {key}")

        if int(obj["step"]) != 199:
            raise AssertionError(f"step mismatch: {obj['step']}")
        if float(obj["elapsed_sec"]) != 100.0:
            raise AssertionError(f"elapsed mismatch: {obj['elapsed_sec']}")
        if abs(float(obj["iter_per_sec"]) - 2.0) > 1e-6:
            raise AssertionError(f"iter_per_sec mismatch: {obj['iter_per_sec']}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: write_throughput_json emits canonical schema")
