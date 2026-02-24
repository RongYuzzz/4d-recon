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
    text = TRAINER.read_text(encoding="utf-8")
    required_tokens = [
        "temporal_corr_npz",
        "lambda_corr",
        "temporal_corr_end_step",
        "temporal_corr_max_pairs",
        "_maybe_load_temporal_corr",
        "_compute_temporal_corr_loss",
        "loss_corr",
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise AssertionError(f"missing strong fusion tokens: {', '.join(missing)}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: strong fusion flags and temporal correspondence loss hooks exist in trainer")
