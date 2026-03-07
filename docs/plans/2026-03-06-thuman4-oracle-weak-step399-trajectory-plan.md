# THUman4 Oracle Weak `step399` Trajectory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 以最小额外成本补齐 `seed41` 与 `seed43` 的 `step399` 中间截面，判断 `oracle backgroundness weak-fusion` 在 `THUman4 / weak-init` 下更像是 baseline 中后段失稳时的 rescue，还是更平滑的 late-emerging / LPIPS-conversion 分叉现象。

**Architecture:** 不改 trainer、不改 gate、不再补 tie-break seed；直接复用现有隔离 worktree `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak` 里的 runner / evaluator，用 **`400-step` 前缀重跑** 来落地 `step399`。这样无需改 `run_train_ours_weak_selfcap.sh` 的保存逻辑，也能得到与 `600-step` 前缀对齐的 `test_step0399.json` 与 `test_step399_*.png`。随后把 `199 / 399 / 599` 三截面结果回填到唯一主文档 `notes/2026-03-06-thuman4-oracle-weak-decision.md`，并同步修正文档里残留的 pre-replication 时态与过重措辞。

**Tech Stack:** Bash runners, Python masked evaluator, THUman4 dataset masks, existing oracle pseudo-mask exporter, JSON audit tables, render packet review.

---

## Scope and non-goals

- **In scope:**
  - `seed41` 与 `seed43` 的 `400-step` baseline / oracle-weak 前缀重跑；
  - 生成 `step399` 的 masked metrics 与代表性 render；
  - 形成 `199 / 399 / 599` 三截面对照表；
  - 更新根仓库唯一主文档 `notes/2026-03-06-thuman4-oracle-weak-decision.md`。
- **Out of scope:**
  - 不补 `seed44`；
  - 不做 `stronger-init sanity check`；
  - 不改 smoke gate；
  - 不改 trainer / runner 代码；
  - 不修改 worktree 里的旧 note 副本。

## Canonical paths and constants

Use exactly these constants everywhere:

```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
ROOT_NOTE=$ROOT/notes/2026-03-06-thuman4-oracle-weak-decision.md
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag
ORACLE_SHARED=$WT/outputs/cue_mining/thuman4_oracle_bg_step399_shared
MAX_STEPS=400
STEP_INDEX=399
PSEUDO_MASK_WEIGHT=0.8
PSEUDO_MASK_END_STEP=600
BOUNDARY_BAND_PX=2
BBOX_MARGIN_PX=32
LPIPS_BACKEND=auto
GPU=0
OMP_NUM_THREADS=1
MASK_DOWNSCALE=4
MASK_THR=0.5
SEEDS=41,43
FRAMES=0000,0015,0030
```

Why `400-step` reruns are acceptable here:
- 当前 worktree 的 baseline runner 支持自定义 `SAVE_STEPS/EVAL_STEPS`，但 oracle weak wrapper 仍默认只在 `MAX_STEPS` 末尾评估与保存；
- trainer 的保存条件是 `step == max_steps - 1` 或命中显式 save list，因此 `MAX_STEPS=400` 会自然落出 `step399` 工件；
- 直接把 `MAX_STEPS=400`，并显式固定 `PSEUDO_MASK_END_STEP=600`，可在**不改脚本**的前提下得到 `step399`，同时保持 weak suppression 覆盖整个 400-step 前缀；
- 这条路线的目的不是取代已有 `600-step` 结论，而是给 `199 -> 599` 之间补一个中间截面。

---

### Task 0: Freeze scope and verify the canonical environment

**Files:**
- Read: `notes/2026-03-06-thuman4-oracle-weak-decision.md`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/run_train_planb_init_selfcap.sh`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/run_train_ours_weak_oracle_bg_selfcap.sh`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/eval_masked_metrics.py`

**Step 1: Verify we are using the worktree implementation, not the root repo scripts**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak

[ -f "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh" ]
[ -f "$WT/scripts/export_oracle_background_pseudo_masks_npz.py" ]
rg -n "boundary_band_px" "$WT/scripts/eval_masked_metrics.py"
```

Expected: all checks pass, and `boundary_band_px` is present in the **worktree** evaluator. If this fails, stop and do not run from the root repo.

**Step 2: Verify root-repo runtime dependencies exist because the commands below bind to them explicitly**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon

[ -x "$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python" ]
[ -d "$ROOT/data/thuman4_subject00_8cam60f/images" ]
[ -d "$ROOT/data/thuman4_subject00_8cam60f/masks" ]
[ -d "$ROOT/data/thuman4_subject00_8cam60f/triangulation" ]
```

Expected: all four checks pass. If any fail, stop before launching training.

**Step 3: Verify existing endpoint artifacts already exist for `seed41` and `seed43`**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak

[ -f "$WT/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/baseline/stats_masked/test_step0199.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/oracle_weak/stats_masked/test_step0199.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/baseline/stats_masked/test_step0199.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/oracle_weak/stats_masked/test_step0199.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s41/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s43/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s43/stats_masked/test_step0599.json" ]
```

Expected: all eight files exist. If not, fix audit paths first.

**Step 4: Create a fresh output root for the mid-trajectory reruns**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
mkdir -p "$WT/outputs/thuman4_oracle_weak_step399_diag"
```

Expected: `outputs/thuman4_oracle_weak_step399_diag` exists and is empty or contains only this plan’s artifacts.

---

### Task 1: Run `seed41` baseline prefix rerun to `step399`

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/baseline/...`

**Step 1: Launch the `400-step` baseline rerun**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag
GPU=0

OMP_NUM_THREADS=1 \
GPU="$GPU" \
SEED=41 \
MAX_STEPS=400 \
DATA_DIR="$DATA" \
VENV_PYTHON="$VENV" \
RESULT_DIR="$OUT/seed41/baseline" \
bash "$WT/scripts/run_train_planb_init_selfcap.sh"
```

Expected: training completes and writes `stats/test_step0399.json` plus `renders/test_step399_*.png`.

**Step 2: Verify the endpoint files exist**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag

[ -f "$OUT/seed41/baseline/stats/test_step0399.json" ]
[ -f "$OUT/seed41/baseline/renders/test_step399_0000.png" ]
[ -f "$OUT/seed41/baseline/renders/test_step399_0015.png" ]
[ -f "$OUT/seed41/baseline/renders/test_step399_0030.png" ]
```

Expected: all four files exist.

---

### Task 2: Run `seed41` oracle-weak prefix rerun to `step399`

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/oracle_weak/...`
- Produce/reuse: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/cue_mining/thuman4_oracle_bg_step399_shared/pseudo_masks.npz`

**Step 1: Launch the `400-step` oracle rerun with the same weak schedule prefix**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag
ORACLE_SHARED=$WT/outputs/cue_mining/thuman4_oracle_bg_step399_shared
GPU=0

OMP_NUM_THREADS=1 \
GPU="$GPU" \
SEED=41 \
MAX_STEPS=400 \
PSEUDO_MASK_WEIGHT=0.8 \
PSEUDO_MASK_END_STEP=600 \
MASK_DOWNSCALE=4 \
MASK_THR=0.5 \
DATA_DIR="$DATA" \
VENV_PYTHON="$VENV" \
RESULT_DIR="$OUT/seed41/oracle_weak" \
ORACLE_DIR="$ORACLE_SHARED" \
bash "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh"
```

Expected: training completes and writes `stats/test_step0399.json`, `renders/test_step399_*.png`, and `pseudo_masks.npz` under `ORACLE_SHARED`.

**Step 2: Verify oracle artifacts exist**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag
ORACLE_SHARED=$WT/outputs/cue_mining/thuman4_oracle_bg_step399_shared

[ -f "$ORACLE_SHARED/pseudo_masks.npz" ]
[ -f "$OUT/seed41/oracle_weak/stats/test_step0399.json" ]
[ -f "$OUT/seed41/oracle_weak/renders/test_step399_0000.png" ]
[ -f "$OUT/seed41/oracle_weak/renders/test_step399_0015.png" ]
[ -f "$OUT/seed41/oracle_weak/renders/test_step399_0030.png" ]
```

Expected: all five files exist.

---

### Task 3: Evaluate `seed41` masked metrics at `step399`

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/baseline/stats_masked/test_step0399.json`
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/oracle_weak/stats_masked/test_step0399.json`

**Step 1: Run masked evaluation for baseline and oracle**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$OUT/seed41/baseline" \
  --stage test --step 399 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$OUT/seed41/oracle_weak" \
  --stage test --step 399 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
```

Expected: both `stats_masked/test_step0399.json` files exist.

**Step 2: Verify required keys exist**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41')
for variant in ['baseline', 'oracle_weak']:
    obj = json.loads((root / variant / 'stats_masked' / 'test_step0399.json').read_text())
    for key in ['psnr_fg_area', 'lpips_fg_comp', 'psnr_bd_area', 'lpips_bd_comp', 'boundary_band_px', 'lpips_backend', 'tlpips']:
        assert key in obj, (variant, key)
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 4: Repeat the same `step399` rerun for `seed43`

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/baseline/...`
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/oracle_weak/...`

**Step 1: Launch `seed43` baseline `400-step` rerun**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag
GPU=0

OMP_NUM_THREADS=1 \
GPU="$GPU" \
SEED=43 \
MAX_STEPS=400 \
DATA_DIR="$DATA" \
VENV_PYTHON="$VENV" \
RESULT_DIR="$OUT/seed43/baseline" \
bash "$WT/scripts/run_train_planb_init_selfcap.sh"
```

Expected: `stats/test_step0399.json` and `renders/test_step399_*.png` exist.

**Step 2: Launch `seed43` oracle `400-step` rerun**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag
ORACLE_SHARED=$WT/outputs/cue_mining/thuman4_oracle_bg_step399_shared
GPU=0

OMP_NUM_THREADS=1 \
GPU="$GPU" \
SEED=43 \
MAX_STEPS=400 \
PSEUDO_MASK_WEIGHT=0.8 \
PSEUDO_MASK_END_STEP=600 \
MASK_DOWNSCALE=4 \
MASK_THR=0.5 \
DATA_DIR="$DATA" \
VENV_PYTHON="$VENV" \
RESULT_DIR="$OUT/seed43/oracle_weak" \
ORACLE_DIR="$ORACLE_SHARED" \
bash "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh"
```

Expected: `stats/test_step0399.json` and `renders/test_step399_*.png` exist.

**Step 3: Run masked evaluation for both `seed43` variants**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_step399_diag

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$OUT/seed43/baseline" \
  --stage test --step 399 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$OUT/seed43/oracle_weak" \
  --stage test --step 399 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
```

Expected: both `stats_masked/test_step0399.json` files exist.

**Step 4: Verify required keys exist**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43')
for variant in ['baseline', 'oracle_weak']:
    obj = json.loads((root / variant / 'stats_masked' / 'test_step0399.json').read_text())
    for key in ['psnr_fg_area', 'lpips_fg_comp', 'psnr_bd_area', 'lpips_bd_comp', 'boundary_band_px', 'lpips_backend', 'tlpips']:
        assert key in obj, (variant, key)
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 5: Build the `199 / 399 / 599` comparison packet

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/summary/triad_summary.json`
- Read: existing `step199` and `step599` masked JSON files from the worktree outputs

**Step 1: Create a machine-readable triad summary for both seeds**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak')
out = root / 'outputs' / 'thuman4_oracle_weak_step399_diag' / 'summary'
out.mkdir(parents=True, exist_ok=True)

spec = {
    '41': {
        '199': root / 'outputs/thuman4_oracle_weak_smoke200_multiseed/seed41',
        '399': root / 'outputs/thuman4_oracle_weak_step399_diag/seed41',
        '599': root / 'outputs/thuman4_oracle_weak_mve',
    },
    '43': {
        '199': root / 'outputs/thuman4_oracle_weak_smoke200_multiseed/seed43',
        '399': root / 'outputs/thuman4_oracle_weak_step399_diag/seed43',
        '599': root / 'outputs/thuman4_oracle_weak_mve',
    },
}

summary = {}
for seed, steps in spec.items():
    summary[seed] = {}
    for step, base_root in steps.items():
        if step == '599':
            base_path = base_root / f'baseline_s{seed}' / 'stats_masked' / 'test_step0599.json'
            oracle_path = base_root / f'oracle_weak_s{seed}' / 'stats_masked' / 'test_step0599.json'
        else:
            base_path = base_root / 'baseline' / 'stats_masked' / f'test_step0{step}.json'
            oracle_path = base_root / 'oracle_weak' / 'stats_masked' / f'test_step0{step}.json'
        base = json.loads(base_path.read_text())
        oracle = json.loads(oracle_path.read_text())
        summary[seed][step] = {
            'baseline': base,
            'oracle': oracle,
            'delta': {
                'psnr_fg_area': float(oracle['psnr_fg_area']) - float(base['psnr_fg_area']),
                'lpips_fg_comp': float(oracle['lpips_fg_comp']) - float(base['lpips_fg_comp']),
                'psnr_bd_area': float(oracle['psnr_bd_area']) - float(base['psnr_bd_area']),
                'lpips_bd_comp': float(oracle['lpips_bd_comp']) - float(base['lpips_bd_comp']),
                'tlpips': float(oracle['tlpips']) - float(base['tlpips']),
            },
        }

(out / 'triad_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(out / 'triad_summary.json')
PY
```

Expected: `summary/triad_summary.json` exists and contains both seeds × three time slices.

**Step 2: Print a compact review table**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
path = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/summary/triad_summary.json')
obj = json.loads(path.read_text())
for seed in ['41', '43']:
    print(f'== seed{seed} ==')
    for step in ['199', '399', '599']:
        d = obj[seed][step]['delta']
        print(
            f"step{step} d_psnr_fg_area={d['psnr_fg_area']:+.6f} "
            f"d_lpips_fg_comp={d['lpips_fg_comp']:+.6f} "
            f"d_psnr_bd_area={d['psnr_bd_area']:+.6f} "
            f"d_lpips_bd_comp={d['lpips_bd_comp']:+.6f} "
            f"d_tlpips={d['tlpips']:+.6f}"
        )
PY
```

Expected: a readable `199 / 399 / 599` delta table for `seed41` and `seed43`.

---

### Task 6: Curate the visual packet for expert diagnosis

**Files:**
- Read/confirm: representative renders for `seed41` and `seed43` at `199 / 399 / 599`
- Update later in root note: `notes/2026-03-06-thuman4-oracle-weak-decision.md`

**Step 1: Verify all representative frames exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak')
checks = []
for seed in ['41', '43']:
    for frame in ['0000', '0015', '0030']:
        checks.extend([
            root / f'outputs/thuman4_oracle_weak_smoke200_multiseed/seed{seed}/baseline/renders/test_step199_{frame}.png',
            root / f'outputs/thuman4_oracle_weak_step399_diag/seed{seed}/baseline/renders/test_step399_{frame}.png',
            root / f'outputs/thuman4_oracle_weak_mve/baseline_s{seed}/renders/test_step599_{frame}.png',
            root / f'outputs/thuman4_oracle_weak_smoke200_multiseed/seed{seed}/oracle_weak/renders/test_step199_{frame}.png',
            root / f'outputs/thuman4_oracle_weak_step399_diag/seed{seed}/oracle_weak/renders/test_step399_{frame}.png',
            root / f'outputs/thuman4_oracle_weak_mve/oracle_weak_s{seed}/renders/test_step599_{frame}.png',
        ])
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`. If not, do not update the note yet.

**Step 2: Write down the exact diagnostic questions before interpreting the data**

Use this checklist when reading `triad_summary.json`:
- Does `seed41` already show strong ROI gain by `step399`, with LPIPS still lagging?
- Does `seed43` cross the LPIPS threshold earlier than `seed41`, or only by `step599`?
- Between `399` and `599`, does baseline degrade, oracle improve, or both?
- Does the main separation appear in `psnr_fg_area`, `psnr_bd_area`, or only in `lpips_fg_comp`?

Expected: interpretation stays anchored to mechanism diagnosis, not route-level re-voting.

---

### Task 7: Update the canonical note with `step399` findings and v5 wording fixes

**Files:**
- Modify: `notes/2026-03-06-thuman4-oracle-weak-decision.md`
- Do **not** modify: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/notes/2026-03-06-thuman4-oracle-weak-decision.md`

**Step 1: Add a new subsection summarizing `step399` evidence**

Insert a new section under the diagnostic appendix / expert addendum that includes:
- why `seed41` and `seed43` were chosen;
- the exact `step399` output root: `WT/outputs/thuman4_oracle_weak_step399_diag/...`;
- a `199 / 399 / 599` triad table for both seeds;
- one short paragraph answering whether the data now looks more like rescue, delayed LPIPS conversion, or true monotonic late emergence.

Expected: the root note can now answer expert follow-ups with a three-time-slice packet instead of only two endpoints.

**Step 2: Fix the stale pre-replication decision text**

Edit the early decision section so it no longer says:
- “如果必须立刻决定，推荐 `B=补最小实验后再决定`”;
- “唯一值得继续投入的是补 2 个非42 seed 的 `600-step` 复核”。

Replace that part with a clearly labeled historical note or superseded summary, e.g.:
```text
This pre-follow-up recommendation is now superseded by the completed 3-seed replication check.
Current route-level status remains: mixed evidence -> stop.
```

Expected: the note contains only one active decision state.

**Step 3: Tighten the mechanism wording per the v5 feedback**

Make these wording changes in the root note:
- change “early-stage background loss suppression” to something closer to
  - **“full-training-window background loss suppression / objective shift”**;
- change “稳定抬升 ROI / boundary 的结构性指标” to a narrower statement such as
  - **“在当前 3 个已审计的 600-step seeds 中，ROI PSNR 一致大幅上升，boundary PSNR 同向为正，但 LPIPS 向改善的转化不稳”**;
- keep `seed41` labeled as
  - **“mixed-evidence seed (gate-fail)”**.

Expected: the note no longer overclaims boundary / LPIPS stability and no longer mixes old decision tenses.

**Step 4: Verify every new file path mentioned in the note exists**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
note = Path('/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md')
missing = []
for line in note.read_text(encoding='utf-8').splitlines():
    if '`' not in line:
        continue
    parts = line.split('`')[1::2]
    for part in parts:
        if part.startswith('/') or part.startswith('.worktrees/') or part.startswith('data/') or part.startswith('outputs/'):
            p = Path('/root/autodl-tmp/projects/4d-recon') / part if not part.startswith('/') else Path(part)
            if ('*.png' in part) or ('...' in part):
                continue
            if not p.exists():
                missing.append(part)
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 8: Final review and stop condition

**Files:**
- Read: `notes/2026-03-06-thuman4-oracle-weak-decision.md`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/summary/triad_summary.json`

**Step 1: Verify the final deliverables exist**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak

[ -f "$ROOT/notes/2026-03-06-thuman4-oracle-weak-decision.md" ]
[ -f "$WT/outputs/thuman4_oracle_weak_step399_diag/summary/triad_summary.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_step399_diag/seed41/baseline/stats_masked/test_step0399.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_step399_diag/seed41/oracle_weak/stats_masked/test_step0399.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_step399_diag/seed43/baseline/stats_masked/test_step0399.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_step399_diag/seed43/oracle_weak/stats_masked/test_step0399.json" ]
```

Expected: all files exist.

**Step 2: Explicitly keep the route-level decision unchanged unless the user asks otherwise**

Expected final interpretation rule:
- `step399` may sharpen the **mechanism explanation**;
- it does **not** reopen the route-level `stop` by itself;
- any future restart proposal must be a separate discussion.

**Step 3: Commit nothing**

Expected: do not `git commit`, do not rewrite historical outputs, do not edit the worktree note copy.

---

## Decision readout guide (after execution)

Use the following interpretation matrix once `triad_summary.json` exists:

- **Case A: `399` already shows large ROI gains in both seeds, but only `seed43` converts to strong LPIPS by `599`**
  - Interpretation: stronger support for **LPIPS-conversion instability / mixed-evidence split** than for pure “late effect”.

- **Case B: baseline worsens sharply from `399 -> 599`, while oracle stays flatter**
  - Interpretation: stronger support for **weak-init rescue / baseline mid-late instability**.

- **Case C: oracle remains close to baseline at `399`, then only separates strongly by `599`**
  - Interpretation: stronger support for a **genuinely delayed effect**, though still not automatically a reproducible line-level positive.

- **Case D: `399` is noisy/inconclusive and visuals do not clarify the split**
  - Interpretation: mechanism remains unresolved; do not expand scope inside this plan.

## Handoff notes

- This plan assumes no code changes are required.
- If execution reveals that `400-step` prefix reruns are not viable or artifacts are missing for reasons not covered here, stop and write a separate code-fix plan instead of improvising.
