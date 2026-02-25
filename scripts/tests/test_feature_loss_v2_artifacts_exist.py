#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    REPO_ROOT / "scripts" / "run_train_feature_loss_v2_selfcap.sh",
    REPO_ROOT / "scripts" / "run_train_feature_loss_v2_gated_selfcap.sh",
    REPO_ROOT / "scripts" / "check_vggt_preprocess_consistency.py",
]


def run_test() -> None:
    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        raise AssertionError("missing v2 artifacts: " + ", ".join(str(p) for p in missing))
    for p in REQUIRED[:2]:
        if not os.access(p, os.R_OK):
            raise AssertionError(f"not readable: {p}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: v2 artifacts exist")
