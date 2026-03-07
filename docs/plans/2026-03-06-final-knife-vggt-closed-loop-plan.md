# Final Knife VGGT Closed-Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用一组最小、受控、可判定成败的 `framediff-gated stage-2` 配对实验，回答 `VGGT-inspired gating` 是否真正对下游 4D 重建优化带来了可辩护收益，从而补上当前项目最关键的“最后一刀”。

**Architecture:** 这不是新的 sweep，而是单一路线的因果测试。以 `ungated stage-2` 为对照、`framediff-gated stage-2` 为处理，只在 `SelfCap` 上跑 `seed42/43` 的 `400-step` 配对，比较 `199/399` 的 `PSNR / LPIPS / tLPIPS`，并按仓库现有噪声带阈值判定是否形成最小正向闭环。

**Tech Stack:** Bash runners, existing `scripts/run_train_planb_feature_loss_v2_selfcap.sh`, existing `scripts/analyze_temporal_diff_from_renders.py`, existing `scripts/analyze_vggt_gate_framediff.py`, `pytest`, Markdown notes.

---

## Scope guardrails

- 只做 `framediff-gated stage-2 paired run` 这一条路线。
- 不新增其他 gating 备选，不扩展到 `full600`，不追加第三个 seed。
- 只允许使用 `SelfCap` 主证据链数据。
- 结果判定必须引用现有 `tLPIPS` 噪声带阈值 `0.001371`。
- 无论结果如何，都只能按 `promising / minimal closed loop / negative-mixed` 三档收口。

---

### Task 0: Create clean execution context

**Files:**
- Read: `AGENTS.md`
- Read: `docs/plans/2026-03-06-final-knife-vggt-closed-loop-design.md`
- Read: `docs/report_pack/2026-02-27-v2/README.md`
- Read: `docs/protocols/protocol_v2.yaml`

**Step 1: Create and enter a dedicated worktree**

Run:
```bash
export MAIN_REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$MAIN_REPO_ROOT"
git worktree add .worktrees/owner-b-20260306-final-knife -b feat/final-knife-vggt-closed-loop
cd .worktrees/owner-b-20260306-final-knife
pwd
```

Expected: all following work happens inside the dedicated worktree.

**Step 2: Pin the shared Python environment**

Run:
```bash
export VENV_PYTHON="${VENV_PYTHON:-$MAIN_REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
[ -x "$VENV_PYTHON" ]
```

Expected: the shared Python interpreter is executable from the worktree.

**Step 3: Freeze the run objective in one sentence**

Write into the work log:

```text
本轮只回答一个问题：framediff-gated stage-2 是否在受控对比里给下游带来了超出噪声带的稳定性收益。
```

Expected: no scope creep into new ablations.

---

### Task 1: Add the paired runner and its contract test

**Files:**
- Create: `scripts/run_planb_feat_v2_framediff400_pair.sh`
- Create: `scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py`
- Read: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
- Read: `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`

**Step 1: Write the failing contract test**

Create `scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py` that asserts the runner contains these exact tokens:
- `MAX_STEPS=400`
- `SEEDS=42,43`
- `LAMBDA_VGGT_FEAT=0.005`
- `VGGT_FEAT_START_STEP=150`
- `VGGT_FEAT_RAMP_STEPS=150`
- `VGGT_FEAT_EVERY=16`
- `VGGT_FEAT_GATING=none`
- `VGGT_FEAT_GATING=framediff`
- `VGGT_FEAT_GATING_TOP_P=0.10`
- `EVAL_STEPS=199,399`
- `SAVE_STEPS=199,399`

**Step 2: Run the test to make sure it fails**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py -q
```

Expected: FAIL because the runner does not yet exist.

**Step 3: Implement the paired runner**

Create `scripts/run_planb_feat_v2_framediff400_pair.sh` with these behaviors:
- `set -euo pipefail`
- loop seeds in `42,43`
- for each seed, run exactly two jobs:
  - `ungated`: `VGGT_FEAT_GATING=none`
  - `gated`: `VGGT_FEAT_GATING=framediff`, `VGGT_FEAT_GATING_TOP_P=0.10`
- fixed defaults:
  - `MAX_STEPS=400`
  - `LAMBDA_VGGT_FEAT=0.005`
  - `VGGT_FEAT_START_STEP=150`
  - `VGGT_FEAT_RAMP_STEPS=150`
  - `VGGT_FEAT_EVERY=16`
  - `EVAL_STEPS=199,399`
  - `SAVE_STEPS=199,399`
- output root:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_framediff400_pair/`

**Step 4: Re-run the contract test**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py -q
```

Expected: PASS.

---

### Task 2: Run the first causal checkpoint on seed42@199

**Files:**
- Read: `docs/report_pack/2026-02-27-v2/README.md`
- Read: `notes/qna.md`

**Step 1: Launch only seed42 paired run first**

Run:
```bash
SEEDS=42 bash scripts/run_planb_feat_v2_framediff400_pair.sh
```

Expected: exactly two run dirs exist for `seed42` (`ungated`, `gated`).

**Step 2: Compare `step199` first and apply the stop rule**

Read the two `test_step0199.json` files and compute:
- `ΔPSNR = gated - ungated`
- `ΔLPIPS = gated - ungated`
- `ΔtLPIPS = gated - ungated`

Hard stop condition:
- `ΔLPIPS > 0`
- `ΔtLPIPS > 0`
- `ΔPSNR <= 0`

If all three are true, stop here: do not add any new settings, do not add any new seed beyond the pre-registered `seed43` confirmation logic.

**Step 3: Record the checkpoint in a note stub**

Create `notes/2026-03-06-final-knife-vggt-closed-loop.md` with a first section:
- `Seed42 step199 checkpoint`
- exact deltas
- whether the stop rule was triggered

Expected: the note now exists even before the full pair finishes.

---

### Task 3: Finish the paired 400-step run

**Files:**
- Modify: `notes/2026-03-06-final-knife-vggt-closed-loop.md`

**Step 1: If seed42 did not hard-fail, run the full pre-registered pair**

Run:
```bash
SEEDS=42,43 bash scripts/run_planb_feat_v2_framediff400_pair.sh
```

Expected: four run dirs exist in total:
- `seed42/ungated`
- `seed42/gated`
- `seed43/ungated`
- `seed43/gated`

**Step 2: Extract the four comparison points**

For each seed, read:
- `step199`
- `step399`

Compute `gated - ungated` for:
- `psnr`
- `lpips`
- `tlpips`

Write them into a compact table in `notes/2026-03-06-final-knife-vggt-closed-loop.md`.

**Step 3: Compute mean delta at step399**

Add one summary block in the note:
- `mean ΔPSNR@399`
- `mean ΔLPIPS@399`
- `mean ΔtLPIPS@399`

Expected: the note now has both per-seed and mean statistics.

---

### Task 4: Optional focused temporal-diff diagnostic

**Files:**
- Read: `scripts/analyze_temporal_diff_from_renders.py`
- Modify: `notes/2026-03-06-final-knife-vggt-closed-loop.md`

**Step 1: Check whether both selected runs exported `test_step399_*.png` renders**

If yes, run exactly one focused diagnostic on the best illustrative seed pair:

```bash
"$VENV_PYTHON" scripts/analyze_temporal_diff_from_renders.py \
  --renders_dir <ungated_run_dir>/renders \
  --pattern_prefix test_step399_ \
  --out_csv outputs/report_pack/diagnostics/final_knife/ungated_temporal_diff_step399.csv

"$VENV_PYTHON" scripts/analyze_temporal_diff_from_renders.py \
  --renders_dir <gated_run_dir>/renders \
  --pattern_prefix test_step399_ \
  --out_csv outputs/report_pack/diagnostics/final_knife/gated_temporal_diff_step399.csv
```

Then write a short delta CSV or a one-paragraph summary in the note.

If no renders exist, do not generate new exports; just record `render diagnostic skipped (no step399 renders)`.

Expected: at most one focused diagnostic packet is produced.

---

### Task 5: Decide whether the last knife succeeded

**Files:**
- Modify: `notes/2026-03-06-final-knife-vggt-closed-loop.md`
- Read: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: Apply the pre-registered success criteria**

Use `tLPIPS` noise-band threshold `0.001371`.

**Strong positive closed loop:**
- both seeds at `step399` satisfy `ΔtLPIPS <= -0.001371`
- both seeds satisfy `ΔLPIPS <= 0`
- both seeds satisfy `ΔPSNR >= 0`

**Minimal thesis-grade closed loop:**
- both seeds at `step399` have `ΔtLPIPS < 0`
- at least one seed satisfies `ΔtLPIPS <= -0.001371`
- neither seed shows meaningful `LPIPS` deterioration
- `mean ΔPSNR >= 0`

**Negative/mixed closed loop:**
- any other outcome

**Step 2: Write exactly one final verdict label**

At the end of the note, choose exactly one:
- `promising positive closed loop`
- `minimal thesis-grade closed loop`
- `negative/mixed closed loop`

**Step 3: Add one sentence about what this means for the thesis**

Template guidance:
- if success: this route can now be described as a genuine optimization bridge, not just an interpretability branch;
- if negative/mixed: this route remains exploratory, but is now closed as a serious negative result rather than an unfinished idea.

---

### Task 6: Feed the result back into the thesis entry pack conservatively

**Files:**
- Modify: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `notes/2026-03-06-final-knife-vggt-closed-loop.md`

**Step 1: Update the VGGT soft-prior brief**

Add one compact paragraph explaining whether the final knife produced:
- a positive optimization bridge,
- or a negative/mixed closed result.

**Step 2: Update the alignment table only if justified**

Allowed conservative promotion rule:
- `注意力/对应关系引导的时空一致约束` may move from `Exploratory` to `Partial` only if the final verdict is `promising positive closed loop` or `minimal thesis-grade closed loop`.

If final verdict is `negative/mixed closed loop`, keep the row as `Exploratory`, but strengthen the evidence column.

**Step 3: Update the README with one line only**

Add a short line under the innovation story stating whether the final knife:
- turned the route into a minimal closed loop,
- or closed it as a negative/mixed result.

**Step 4: Verify no overclaim was introduced**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/README.md').read_text(encoding='utf-8')
for bad in ['已证明 stage-2 全面有效', '稳定全面优于', '完整证明原版开题全部成立']:
    assert bad not in text, bad
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 7: Final acceptance check

**Files:**
- Read: `notes/2026-03-06-final-knife-vggt-closed-loop.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Verify final-knife deliverables exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    'scripts/run_planb_feat_v2_framediff400_pair.sh',
    'scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py',
    'notes/2026-03-06-final-knife-vggt-closed-loop.md',
]
missing = [p for p in checks if not Path(p).exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

**Step 2: Re-answer the only core question**

The note must let you answer exactly one sentence:

```text
VGGT-inspired gating 是否已经在受控对比里，形成了一个可辩护的下游收益闭环？
```

Expected: the answer is now explicit, regardless of whether it is yes or no.

**Step 3: Do not commit unless explicitly asked**

Expected: no `git commit` is made unless the user later requests it.
