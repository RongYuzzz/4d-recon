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
RUN_STRONG_SCRIPT = REPO_ROOT / "scripts" / "run_train_ours_strong_selfcap.sh"


def run_test() -> None:
    trainer_text = TRAINER.read_text(encoding="utf-8")
    required_trainer_tokens = [
        "temporal_corr_npz",
        "lambda_corr",
        "temporal_corr_end_step",
        "temporal_corr_max_pairs",
        "temporal_corr_loss_mode",
        "temporal_corr_gate_pseudo_mask: bool = False",
        "temporal_corr_pred_pred_detach_target: bool = False",
        "pred_pred",
        "_maybe_load_temporal_corr",
        "_compute_temporal_corr_loss",
        "loss_corr",
    ]
    missing_trainer = [token for token in required_trainer_tokens if token not in trainer_text]
    if missing_trainer:
        raise AssertionError(
            "missing strong fusion tokens in trainer: " + ", ".join(missing_trainer)
        )

    run_script_text = RUN_STRONG_SCRIPT.read_text(encoding="utf-8")
    required_script_tokens = [
        "TEMPORAL_CORR_LOSS_MODE",
        "TEMPORAL_CORR_GATE_PSEUDO_MASK",
        "TEMPORAL_CORR_PRED_PRED_DETACH_TARGET",
        "--temporal-corr-loss-mode",
        "--temporal-corr-gate-pseudo-mask",
        "--temporal-corr-pred-pred-detach-target",
    ]
    missing_script = [token for token in required_script_tokens if token not in run_script_text]
    if missing_script:
        raise AssertionError(
            "missing strong fusion tokens in run script: " + ", ".join(missing_script)
        )


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: strong fusion flags and temporal correspondence loss hooks exist in trainer")
