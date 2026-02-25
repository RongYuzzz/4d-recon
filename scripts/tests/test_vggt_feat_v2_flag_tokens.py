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
        "token_proj",
        "vggt_feat_loss_type",
        "vggt_feat_ramp_steps",
        "vggt_feat_gating_top_p",
        "gate_framediff",
    ]
    missing = [token for token in required_tokens if token not in trainer_text]
    if missing:
        raise AssertionError("missing VGGT v2 tokens in trainer: " + ", ".join(missing))


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: VGGT feature-loss v2 tokens exist in trainer")
