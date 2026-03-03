#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINER = (
    REPO_ROOT
    / "third_party"
    / "FreeTimeGsVanilla"
    / "src"
    / "simple_trainer_freetime_4d_pure_relocation.py"
)


def run_test() -> None:
    trainer_text = TRAINER.read_text(encoding="utf-8")
    required_tokens = [
        "export_vel_filter",
        "export_vel_threshold",
        "_maybe_apply_export_vel_filter",
        "export_from_checkpoint",
        "--export-only",
    ]
    missing = [token for token in required_tokens if token not in trainer_text]
    if missing:
        raise AssertionError("missing export velocity-filter tokens in trainer: " + ", ".join(missing))


def test_export_vel_filter_flags() -> None:
    run_test()


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: export velocity-filter flags and hooks exist in trainer")
