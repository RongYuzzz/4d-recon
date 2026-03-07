# THUman4 Oracle Weak Follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用最小额外成本验证 `seed42` 的 `600-step` 正例是否可复现，并在不改 gate、不追加 200-step 权重扫的前提下，对 `oracle backgroundness weak-fusion` 做出继续/停止决策。

**Architecture:** 先冻结当前证据口径，只在现有 worktree 中补做 `2` 个非 `42` seed 的 `600-step` baseline vs oracle-weak 对照，保持数据、脚本、评估参数、阈值完全一致；随后把 `3-seed 600-step` 结果回填到唯一讨论主文档 `/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md`，再按预先写明的决策规则判断是 stop 还是升级为“weak-init 下可复现的 late-emerging weak positive”。整个计划不做任何代码改动，不改 smoke gate，不新增 200-step sweeps。

**Tech Stack:** Bash runners, Python eval script, existing worktree `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak`, THUman4 dataset, JSON stats audit.

---

### Task 0: Freeze scope and verify preflight

**Files:**
- Read: `/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/run_train_planb_init_selfcap.sh`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/run_train_ours_weak_oracle_bg_selfcap.sh`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/eval_masked_metrics.py`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/scripts/export_oracle_background_pseudo_masks_npz.py`

**Step 1: Confirm the only next experiment is `2-seed 600` and lock the canonical note path**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
ROOT_NOTE=$ROOT/notes/2026-03-06-thuman4-oracle-weak-decision.md
sed -n '1,260p' "$ROOT_NOTE"
```

Expected: 文档明确写着“`late-emerging` 目前只是待验证假说”，且“唯一值得继续投入的下一步是补 `2` 个非 `42` seed 的 `600-step` 复核”；并且后续只更新 `ROOT_NOTE`，**不要更新** worktree 里的旧副本。

**Step 2: Verify root note, worktree, venv, dataset masks, scripts, and seed42 reference artifacts exist**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
ROOT_NOTE=$ROOT/notes/2026-03-06-thuman4-oracle-weak-decision.md

[ -f "$ROOT_NOTE" ]
[ -d "$WT" ]
[ -x "$VENV" ]
[ -d "$DATA/images" ]
[ -d "$DATA/masks" ]
[ -d "$DATA/triangulation" ]
[ -f "$WT/scripts/run_train_planb_init_selfcap.sh" ]
[ -f "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh" ]
[ -f "$WT/scripts/eval_masked_metrics.py" ]
[ -f "$WT/scripts/export_oracle_background_pseudo_masks_npz.py" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s42/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s42/stats_masked/test_step0599.json" ]
```

Expected: 全部返回成功；如果这里失败，不要开跑新 seed。

**Step 3: Freeze execution constants**

Use exactly these constants for every new run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
ROOT_NOTE=$ROOT/notes/2026-03-06-thuman4-oracle-weak-decision.md
MAX_STEPS=600
LPIPS_BACKEND=auto
BOUNDARY_BAND_PX=2
BBOX_MARGIN_PX=32
OMP_NUM_THREADS=1
SECOND_SEED=43
SECOND_SEED_FALLBACK=44
```

Expected: 后续所有命令严格复用同一套常量，不临时换数据、不改评估参数。

**Step 4: Pick concrete seeds and reserve one backup seed**

Use:
```text
primary seeds: 41, 43
backup seed: 44
```

Expected: 除非 `43` 因环境/作业失败不可用，否则不要改 seed 选择；如果启用 `44`，后续所有汇总命令都必须把 `SECOND_SEED=44` 一并带上。

**Step 5: Commit nothing and keep note updates in the root repo only**

Expected: 本计划只追加 `outputs/` 工件和更新 `ROOT_NOTE`，不做代码提交，也不改 worktree 里的旧版 note。

---

### Task 1: Run full `600-step` baseline vs oracle-weak for `seed41`

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s41/...`
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/...`
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/cue_mining/thuman4_oracle_bg_s41/...`

**Step 1: Run `seed41` baseline 600**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

OMP_NUM_THREADS=1 SEED=41 MAX_STEPS=600 DATA_DIR="$DATA" VENV_PYTHON="$VENV" \
  RESULT_DIR="$WT/outputs/thuman4_oracle_weak_mve/baseline_s41" \
  bash "$WT/scripts/run_train_planb_init_selfcap.sh"

[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s41/stats/test_step0599.json" ]
```

Expected: 训练正常完成，并生成 `stats/test_step0599.json`；如果该文件不存在，立刻停在这里排查，不要继续跑 oracle weak。

**Step 2: Run `seed41` oracle weak 600**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

OMP_NUM_THREADS=1 SEED=41 MAX_STEPS=600 DATA_DIR="$DATA" VENV_PYTHON="$VENV" \
  RESULT_DIR="$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s41" \
  ORACLE_DIR="$WT/outputs/cue_mining/thuman4_oracle_bg_s41" \
  bash "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh"

[ -f "$WT/outputs/cue_mining/thuman4_oracle_bg_s41/pseudo_masks.npz" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/stats/test_step0599.json" ]
```

Expected: 训练正常完成，并生成 `stats/test_step0599.json`；oracle runner 会自动创建 `pseudo_masks.npz`，若缺失也应在这里立刻停下。

**Step 3: Evaluate masked metrics for both runs**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$WT/outputs/thuman4_oracle_weak_mve/baseline_s41" \
  --stage test --step 599 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s41" \
  --stage test --step 599 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
```

Expected: 两边都生成 `stats_masked/test_step0599.json`。

**Step 4: Verify required masked keys exist**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve')
for name in ['baseline_s41', 'oracle_weak_s41']:
    obj = json.loads((root / name / 'stats_masked' / 'test_step0599.json').read_text())
    for key in ['psnr_fg_area', 'lpips_fg_comp', 'psnr_bd_area', 'lpips_bd_comp', 'tlpips']:
        assert key in obj, (name, key)
print('ok')
PY
```

Expected: 输出 `ok`。

**Step 5: Do not interpret yet**

Expected: 只检查文件是否完整，不在这个任务里下结论。

---

### Task 2: Run full `600-step` baseline vs oracle-weak for `seed43`

**Files:**
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s43/...`
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s43/...`
- Produce: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/cue_mining/thuman4_oracle_bg_s43/...`

**Step 1: Run `seed43` baseline 600**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

OMP_NUM_THREADS=1 SEED=43 MAX_STEPS=600 DATA_DIR="$DATA" VENV_PYTHON="$VENV" \
  RESULT_DIR="$WT/outputs/thuman4_oracle_weak_mve/baseline_s43" \
  bash "$WT/scripts/run_train_planb_init_selfcap.sh"

[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s43/stats/test_step0599.json" ]
```

Expected: 训练正常完成，并生成 `stats/test_step0599.json`；如果该文件不存在，立刻停在这里排查，不要继续跑 oracle weak。

**Step 2: Run `seed43` oracle weak 600**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

OMP_NUM_THREADS=1 SEED=43 MAX_STEPS=600 DATA_DIR="$DATA" VENV_PYTHON="$VENV" \
  RESULT_DIR="$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s43" \
  ORACLE_DIR="$WT/outputs/cue_mining/thuman4_oracle_bg_s43" \
  bash "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh"

[ -f "$WT/outputs/cue_mining/thuman4_oracle_bg_s43/pseudo_masks.npz" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s43/stats/test_step0599.json" ]
```

Expected: 训练正常完成，并生成 `stats/test_step0599.json`；oracle runner 会自动创建 `pseudo_masks.npz`，若缺失也应在这里立刻停下。

**Step 3: Evaluate masked metrics for both runs**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$WT/outputs/thuman4_oracle_weak_mve/baseline_s43" \
  --stage test --step 599 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s43" \
  --stage test --step 599 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
```

Expected: 两边都生成 `stats_masked/test_step0599.json`。

**Step 4: Verify required masked keys exist**

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve')
for name in ['baseline_s43', 'oracle_weak_s43']:
    obj = json.loads((root / name / 'stats_masked' / 'test_step0599.json').read_text())
    for key in ['psnr_fg_area', 'lpips_fg_comp', 'psnr_bd_area', 'lpips_bd_comp', 'tlpips']:
        assert key in obj, (name, key)
print('ok')
PY
```

Expected: 输出 `ok`。

**Step 5: If `seed43` run is invalid, use backup `seed44` instead**

Run the same command set with `SEED=44` and corresponding output suffixes only if `seed43` 因环境问题无法形成完整 baseline/oracle/eval 三件套；一旦启用备用 seed，后续 Task 3 与 Task 5 的命令都必须显式带上：
```bash
SECOND_SEED=44
```

Expected: 最终拿到两个新 seed 的完整 `600-step` 对照结果，并且后续汇总不会误读不存在的 `seed43` 路径。

---

### Task 3: Build the `3-seed 600-step` decision table

**Files:**
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/*/stats_masked/test_step0599.json`
- Modify: `/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md`

**Step 1: Compute deltas for seeds `42`, `41`, and `SECOND_SEED`**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
SECOND_SEED="${SECOND_SEED:-43}"

SECOND_SEED="$SECOND_SEED" python3 - <<'PY'
import json
import os
from pathlib import Path
root = Path('/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve')
second_seed = int(os.environ['SECOND_SEED'])
seeds = [42, 41, second_seed]
for seed in seeds:
    base = json.loads((root / f'baseline_s{seed}' / 'stats_masked' / 'test_step0599.json').read_text())
    weak = json.loads((root / f'oracle_weak_s{seed}' / 'stats_masked' / 'test_step0599.json').read_text())
    d = {
        'd_psnr_fg_area': float(weak['psnr_fg_area']) - float(base['psnr_fg_area']),
        'd_lpips_fg_comp': float(weak['lpips_fg_comp']) - float(base['lpips_fg_comp']),
        'd_psnr_bd_area': float(weak['psnr_bd_area']) - float(base['psnr_bd_area']),
        'd_lpips_bd_comp': float(weak['lpips_bd_comp']) - float(base['lpips_bd_comp']),
        'd_tlpips': float(weak['tlpips']) - float(base['tlpips']),
    }
    passed = (
        d['d_psnr_fg_area'] >= 0.2 and
        d['d_lpips_fg_comp'] <= -0.003 and
        d['d_tlpips'] <= 0.01 and
        (d['d_psnr_bd_area'] >= 0.2 or d['d_lpips_bd_comp'] <= -0.001)
    )
    print(f"seed={seed} pass={passed} " + " ".join(f"{k}={v:+.6f}" for k, v in d.items()))
PY
```

Expected: 输出 `seed42`、`seed41`、`seed43`（或 `seed44`）的同口径 `600-step` delta 和 pass/fail。

**Step 2: Summarize the replication count**

Interpret with this rule:
```text
replicated = number of non-42 seeds that also pass the same 600-step gate
```

Expected: 得到 `replicated = 0/2`、`1/2` 或 `2/2` 的清晰结果。

**Step 3: Update the single discussion document, not a new conclusion file**

Append/update `/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md` with:
- 新增 `seed41`、`seed43`（或 `44`）的 `600-step` delta 行
- `3-seed 600-step` 的 pass count
- “late-emerging” 是否仍只是弱线索，还是升级为可复现现象
- 明确写出下一决策：`stop` or `continue to one broader validation`

Expected: 所有讨论所需关键信息仍集中在同一份根仓库主文档中；**不要更新** `$WT/notes/2026-03-06-thuman4-oracle-weak-decision.md`。

**Step 4: Keep wording discipline**

Expected wording rules:
- 若 `replicated < 2/2`：不得写“late-emerging 已证实”
- 若 `replicated = 2/2`：也只能写“在 THUman4 / weak init 下可复现”，不得外推到 SelfCap 或正常初始化

**Step 5: Do not edit historical outputs**

Expected: 只追加新目录，不手改任何 `outputs/` 历史结果。

---

### Task 4: Make the next checkpoint decision

**Files:**
- Modify: `/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md`
- Optionally create: `docs/plans/2026-03-06-selfcap-mask-readiness-plan.md` (only if current line survives)

**Step 1: If replication fails, stop immediately**

Decision rule:
```text
if replicated == 0/2:
    stop the oracle-weak line
```

Expected: 文档明确写出 `seed42` 属于离群值/不足以支持路线继续，后续不再投入这条线。

**Step 2: If replication is mixed, treat as weak evidence and stop line-level investment**

Decision rule:
```text
if replicated == 1/2:
    do not change gate
    do not broaden the line
    stop line-level investment unless a supervisor explicitly requests one last tie-break seed
```

Expected: 结论仍偏保守，不把 mixed evidence 包装成可复现信号。

**Step 3: If replication succeeds, allow exactly one broader validation**

Decision rule:
```text
if replicated == 2/2:
    keep current smoke gate unchanged
    approve exactly one broader validation task
```

That single broader validation should be chosen in this priority order:
1. `SelfCap` mask-readiness plan（先补齐 `masks/` 前提，回答原始问题）
2. 或者 one stronger-init sanity check（验证这是否只是 weak-init rescue）

Expected: 即使 `2/2` 复现，也不直接改 gate，不直接扩线做大规模 sweep。

**Step 4: Record the reason for whichever branch is chosen**

Expected: 主文档必须明确写出：
- 为什么 stop / continue
- 为什么不改 smoke gate
- 为什么不继续做 `200-step` 权重扫
- 为什么只更新根仓库主 note，而不是 worktree 里的旧副本

**Step 5: Only after the decision note is updated, prepare discussion prompt**

Expected: 对外讨论材料以更新后的主文档为唯一事实底稿，不提前生成过时 prompt。

---

### Task 5: Verification before handoff

**Files:**
- Read: `/root/autodl-tmp/projects/4d-recon/notes/2026-03-06-thuman4-oracle-weak-decision.md`
- Read: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/*/stats_masked/test_step0599.json`

**Step 1: Check all expected `600-step` artifacts exist**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
SECOND_SEED="${SECOND_SEED:-43}"

find "$WT/outputs/thuman4_oracle_weak_mve" -path '*/stats_masked/test_step0599.json' | sort
[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s42/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s42/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s41/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/baseline_s${SECOND_SEED}/stats_masked/test_step0599.json" ]
[ -f "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s${SECOND_SEED}/stats_masked/test_step0599.json" ]
```

Expected: 至少看到 `baseline_s42/oracle_weak_s42` 加上两个新 seed 的 baseline/oracle 共 `6` 个 masked stats 文件；如果启用了备用 seed，这里也必须随 `SECOND_SEED=44` 一起检查。

**Step 2: Re-open the final decision note and verify consistency**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
ROOT_NOTE=$ROOT/notes/2026-03-06-thuman4-oracle-weak-decision.md
sed -n '1,320p' "$ROOT_NOTE"
```

Expected: 根仓库主文档中的结论与实际 `3-seed 600-step` 结果一致，没有把假说写成结论。

**Step 3: Verify no unrelated files were touched in either repo view**

Run:
```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak

git -C "$ROOT" status --short
git -C "$WT" status --short
```

Expected: 根仓库只看到预期的计划/主 note 更新，worktree 只看到新增 `outputs/` 工件及必要范围内的改动；不应出现手工改写旧结果的痕迹。

**Step 4: Handoff summary**

The handoff must state exactly:
- `seed42/600` 是否被另外 `2` 个 seed 复现
- 第二个新增 seed 实际使用的是 `43` 还是 `44`
- 最终决策是 `stop` 还是 `continue to one broader validation`
- 如果继续，唯一批准的下一件事是什么

**Step 5: Commit nothing unless explicitly requested**

Expected: 默认不提交代码或文档变更。
