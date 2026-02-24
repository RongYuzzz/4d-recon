#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_PIPELINE = REPO_ROOT / "third_party" / "FreeTimeGsVanilla" / "run_pipeline.sh"


def run_test() -> None:
    text = RUN_PIPELINE.read_text(encoding="utf-8")
    required_tokens = [
        "RENDER_TRAJ_PATH",
        "--render-traj-path",
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise AssertionError(f"missing run_pipeline render env support: {', '.join(missing)}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: run_pipeline supports render trajectory env flags")
