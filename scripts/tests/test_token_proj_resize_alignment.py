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
HELPER_NAME = "_token_proj_project_and_resize"


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
    assert callable(helper), "helper should be callable"

    g = torch.Generator(device="cpu")
    g.manual_seed(20260225)

    s = 8
    patch_h0 = 37
    patch_w0 = 37
    n_patch = patch_h0 * patch_w0
    d = 96
    proj_dim = 32
    hf = 9
    wf = 9

    patch_tokens = torch.randn((s, n_patch, d), generator=g, dtype=torch.float32)
    w = torch.randn((proj_dim, d), generator=g, dtype=torch.float32)

    ref_proj = torch.einsum("pd,snd->snp", w, patch_tokens)
    ref = ref_proj.reshape(s, patch_h0, patch_w0, proj_dim).permute(0, 3, 1, 2).contiguous()
    ref = F.interpolate(ref, size=(hf, wf), mode="bilinear", align_corners=False)

    out = helper(
        patch_tokens_snd=patch_tokens,
        w=w,
        patch_h0=patch_h0,
        patch_w0=patch_w0,
        hf=hf,
        wf=wf,
    )
    if tuple(out.shape) != (s, proj_dim, hf, wf):
        raise AssertionError(f"unexpected output shape: {tuple(out.shape)}")

    diff = (out - ref).abs().max().item()
    if diff >= 1e-5:
        raise AssertionError(f"max_abs_diff too large: {diff}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: token_proj resize alignment is correct")
