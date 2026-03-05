#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINER = (
    REPO_ROOT
    / "third_party"
    / "FreeTimeGsVanilla"
    / "src"
    / "simple_trainer_freetime_4d_pure_relocation.py"
)
HELPER_NAME = "_vggt_feat_downsample_dense_gate"


def _load_helper() -> object:
    src = TRAINER.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(TRAINER))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == HELPER_NAME:
            fn_src = ast.get_source_segment(src, node)
            if not fn_src:
                raise AssertionError(f"failed to extract source for {HELPER_NAME}")
            ns: dict[str, object] = {"torch": torch, "F": F, "Tensor": torch.Tensor}
            exec("from __future__ import annotations\n" + fn_src, ns)  # noqa: S102
            return ns[HELPER_NAME]
    raise AssertionError(f"missing helper in trainer: {HELPER_NAME}")


def run_test() -> None:
    helper = _load_helper()
    g = torch.Generator(device="cpu")
    g.manual_seed(20260305)
    mask = (torch.rand((2, 1, 32, 40), generator=g) > 0.7).float()
    out = helper(mask, hf=8, wf=9)
    assert tuple(out.shape) == (2, 1, 8, 9)
    assert float(out.min()) >= 0.0
    assert float(out.max()) <= 1.0


def test_vggt_dense_gate_downsample_helper() -> None:
    run_test()


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: vggt dense gate downsample helper exists and is bounded")
