#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "run_train_planb_feature_loss_v2_selfcap.sh"


def run_test() -> None:
    if not SCRIPT.exists():
        raise AssertionError(f"missing runner script: {SCRIPT}")
    text = SCRIPT.read_text(encoding="utf-8")
    required_tokens = [
        "init_velocity_from_points.py",
        "--init-npz-path \"$PLANB_INIT_NPZ\"",
        "--vggt-feat-cache-npz",
        "--lambda-vggt-feat",
        "feature loss will never run",
        "framediff top-p mismatch",
        "outputs/protocol_v2",
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise AssertionError("runner script missing required tokens: " + ", ".join(missing))


def test_run_train_planb_feature_loss_v2_script_exists() -> None:
    run_test()


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: planb+feature-loss v2 runner exists and references expected flags")
