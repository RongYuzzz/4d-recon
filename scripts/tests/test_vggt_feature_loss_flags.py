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
        "vggt_feat_cache_npz",
        "lambda_vggt_feat",
        "vggt_feat_start_step",
        "vggt_feat_every",
        "vggt_feat_phi_name",
        "vggt_feat_patch_k",
        "vggt_feat_patch_hw",
        "vggt_feat_use_conf",
        "vggt_feat_gating",
        "_maybe_load_vggt_feat_cache",
        "_compute_vggt_feature_loss",
        "loss_feat",
    ]
    missing = [token for token in required_tokens if token not in trainer_text]
    if missing:
        raise AssertionError("missing VGGT feature-loss tokens in trainer: " + ", ".join(missing))


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: VGGT feature-loss flags and hooks exist in trainer")
