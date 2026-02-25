#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from precompute_vggt_cache import _project_patch_tokens  # noqa: E402


def run_test() -> None:
    rng = np.random.default_rng(20260225)
    tokens = rng.standard_normal((2, 64, 96), dtype=np.float32)

    out_a = _project_patch_tokens(tokens, proj_dim=24, proj_seed=1234)
    out_b = _project_patch_tokens(tokens, proj_dim=24, proj_seed=1234)
    out_c = _project_patch_tokens(tokens, proj_dim=24, proj_seed=5678)

    if out_a.shape != (2, 64, 24):
        raise AssertionError(f"unexpected output shape: {out_a.shape}")
    if not np.allclose(out_a, out_b, atol=0.0, rtol=0.0):
        raise AssertionError("same seed should produce identical token projection outputs")
    if np.allclose(out_a, out_c, atol=1e-7, rtol=1e-6):
        raise AssertionError("different seeds should produce different token projection outputs")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: token-proj projection is deterministic by seed")
