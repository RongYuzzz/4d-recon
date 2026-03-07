# VGGT Cue-Soft Go/No-Go Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 只重开一条最小路线：把 `stage-2 VGGT feature loss` 的 gating 从错误对齐的 `framediff top-p`，改成 **VGGT cue-backed dense soft weighting (`cue_soft`)**，然后在 `SelfCap / seed42,43 / 400-step` 上做一次严格 go/no-go 判定。

**Architecture:** 这不是新的 sweep，也不是继续修 `local-softmatch family`。唯一要验证的是：如果把 feature loss 的施压区域改成更贴近 ROI 的 `VGGT cue soft weight`，而不是 `framediff hard top-p`，是否终于能在主证据场 `SelfCap` 上产生超出噪声带的最小正信号。为避免把“信号源选择”和“损失几何”混在一起，这次 treatment 继续使用 `token_proj + cosine`，不再引入 `local-softmatch`、不再引入 `framediff`、不再加第二种训练损失。

**Tech Stack:** PyTorch trainer under `third_party/FreeTimeGsVanilla/`, existing cue-mining NPZ tooling, Bash runners in `scripts/`, `pytest`, Markdown notes under `notes/`, protocol_v2 stats JSON outputs.

---

## Scope guardrails

- 这次只允许重开 **一条** 新路线：`cue_soft`。
- 不再继续 `local-softmatch family`；不再继续 `framediff top-p`；不把这两条旧路线混进 treatment。
- 不引入 `lambda_corr` / temporal correspondence loss，不把 KLT strong 重新拉回主战场。
- Treatment 固定为：`token_proj + cosine + cue_soft + lambda=0.005 + start=150 + ramp=150 + every=16`。
- Control 固定为：`no extra VGGT optimization loss`。
- 数据与预算固定：`SelfCap`、`seed42,43`、`400-step`。
- 主 cache 先固定使用现有 `ds4`（`phi_size=9x9`）版本；这次不再把 `phi_size` 升级和新 gating 一起绑成多变量实验。
- cue 输入固定来自：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz`，但在训练前必须离线缩放成更可用的 soft mask。
- `outputs/` 只新增 append-only 路径，不得覆盖任何旧结果目录。
- 最终判据继续沿用当前 thesis closeout 口径：`mean ΔtLPIPS@399 <= -0.001371`、`mean ΔLPIPS@399 <= 0`、`mean ΔPSNR@399 >= 0`、且两颗 seed 的 `ΔtLPIPS@399 < 0`。
- 如果这次 `cue_soft` rerun 仍然 `STOP`，则**当前 SelfCap cue-soft route** 在本项目内关闭；不允许立刻用“再调一点 quantile / λ / top-p / step”重开同一路线。

## Why this route, not the others

- 现有证据显示，`framediff gate` 与 `token_proj` cosine loss 更像 **signal mismatch**，而不是简单超参没调好。
- 现有证据也显示，`local-softmatch family` 已经做过公平复核，仍是 `STOP`；因此这次不再动 loss 几何，而是换 **signal/ROI 对齐假设**。
- 当前 correspondence 证据（KLT / token-topk）更适合做解释或后续增强，不适合直接作为这次唯一最小重开路线的主输入。
- 因此，这次路线定义为：**先用已有 VGGT cue probe 作为 ROI-like soft prior，直接测试“选区错位”是不是主矛盾。**

---

### Task 0: Create the rerun worktree from the correct baseline and freeze the question

**Files:**
- Read: `AGENTS.md`
- Read: `notes/feature_loss_failure_attribution_minpack.md`
- Read: `notes/openproposal_phase6_fg_realign_phase4.md`
- Read: `$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-final-knife/notes/2026-03-06-final-knife-vggt-closed-loop.md`
- Read: `$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-vggt-softmatch-lossfix/notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md`

**Step 1: Create and enter a dedicated worktree from the Phase6 tooling baseline**

Run:
```bash
export MAIN_REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$MAIN_REPO_ROOT"
git worktree add -b feat/vggt-cuesoft-go-nogo \
  .worktrees/owner-b-20260307-vggt-cuesoft-go-nogo \
  owner-b-20260305-fg-realign
cd .worktrees/owner-b-20260307-vggt-cuesoft-go-nogo
pwd
```

Expected:
- new worktree is created from `owner-b-20260305-fg-realign`;
- this is intentional because that baseline already contains `scale_pseudo_masks_npz.py`, `mask_healthcheck_sweep.py`, and the improved masked-metrics tooling;
- all following work happens inside `.worktrees/owner-b-20260307-vggt-cuesoft-go-nogo`.

**Step 2: Pin the shared Python environment**

Run:
```bash
export VENV_PYTHON="${VENV_PYTHON:-$MAIN_REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
[ -x "$VENV_PYTHON" ]
```

Expected: the shared interpreter is executable, and `MAIN_REPO_ROOT` remains exported for all later commands that need shared `data/` and historical `outputs/` inputs.

**Step 3: Verify the cue source and calibration tools exist before coding**

Run:
```bash
[ -d "$MAIN_REPO_ROOT/data/selfcap_bar_8cam60f" ]
[ -f "$MAIN_REPO_ROOT/outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz" ]
[ -f "$MAIN_REPO_ROOT/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz" ]
[ -f "$MAIN_REPO_ROOT/outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz" ]
[ -f scripts/scale_pseudo_masks_npz.py ]
[ -f scripts/mask_healthcheck_sweep.py ]
```

Expected: all six checks pass.

**Step 4: Freeze the one-sentence route question in the work log**

Write this sentence into the execution log before coding:

```text
本轮只回答一个问题：如果把 VGGT feature loss 的选区从 framediff hard-gate 改成 cue-backed dense soft weighting、其余训练形状保持不变，SelfCap 上是否会出现超出噪声带的最小正信号。
```

Expected: no drift into local-softmatch reruns or correspondence-loss rewrites.

---

### Task 1: Prepare a scaled SelfCap cue source and audit that it is non-degenerate

**Files:**
- Read: `$MAIN_REPO_ROOT/outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz`
- Read: `$MAIN_REPO_ROOT/outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
- Read: `scripts/scale_pseudo_masks_npz.py`
- Read: `scripts/mask_healthcheck_sweep.py`
- Create: `notes/2026-03-07-vggt-cuesoft-go-nogo.md`

**Step 1: Generate one scaled cue NPZ for training**

Run:
```bash
"$VENV_PYTHON" scripts/scale_pseudo_masks_npz.py \
  --in_npz "$MAIN_REPO_ROOT/outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks.npz" \
  --out_npz outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks_dyn_q0p95_scaled.npz \
  --quantile 0.95 \
  --mode dynamic_scaled \
  --overwrite
```

Expected: `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks_dyn_q0p95_scaled.npz` exists.

**Step 2: Conditionally run the silhouette healthcheck only if SelfCap GT masks are actually present**

Run:
```bash
if [ -d "$MAIN_REPO_ROOT/data/selfcap_bar_8cam60f/masks/09" ]; then
  "$VENV_PYTHON" scripts/mask_healthcheck_sweep.py \
    --data_dir "$MAIN_REPO_ROOT/data/selfcap_bar_8cam60f" \
    --pred_mask_npz outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks_dyn_q0p95_scaled.npz \
    --camera 09 \
    --out_json outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks_dyn_q0p95_scaled_healthcheck_cam09.json
else
  echo '[CueSoft] SelfCap masks missing; skip silhouette healthcheck and rely on cue distribution audit only.'
fi
```

Expected:
- if `SelfCap` GT masks exist, the healthcheck JSON exists;
- otherwise the command prints the skip line and the note explicitly records that `SelfCap` currently lacks dataset silhouettes, so preflight is based on cue-distribution audit rather than mIoU.

**Step 3: Record a tiny non-degeneracy audit into the note stub**

Create `notes/2026-03-07-vggt-cuesoft-go-nogo.md` with these mandatory stub sections:
- `Question`
- `Why this route exists`
- `Cue source`
- `Cue scaling audit`
- `Silhouette healthcheck status`
- `Exact config`
- `Current status`

Then run and record these raw numbers into the note:
```bash
python3 - <<'PY'
import json, numpy as np, os
from pathlib import Path
main_repo_root = Path(os.environ['MAIN_REPO_ROOT'])
q = json.loads((main_repo_root / 'outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json').read_text())
with np.load('outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks_dyn_q0p95_scaled.npz', allow_pickle=True) as d:
    masks = d['masks'].astype('float32')
print('raw_all_black', q['all_black'])
print('raw_all_white', q['all_white'])
print('raw_mask_max', q['mask_max'])
print('selfcap_masks_exist', (main_repo_root / 'data/selfcap_bar_8cam60f/masks/09').is_dir())
print('scaled_mean', float(masks.mean()))
print('scaled_max', float(masks.max()))
PY
```

Expected:
- raw cue is not all-black/all-white;
- scaled cue has a non-zero mean and max > 0;
- the note explicitly records whether `SelfCap` GT masks were available or skipped;
- the note explicitly records which NPZ will be used by the rerun.

---

### Task 2: Add contract tests for the new `cue_soft` gating route before implementation

**Files:**
- Create: `scripts/tests/test_vggt_feat_cuesoft_gate_contract.py`
- Modify: `scripts/tests/test_vggt_feature_loss_flags.py`
- Modify: `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`
- Modify: `scripts/tests/test_runner_args_passthrough.py`

**Step 1: Write the new trainer contract test first**

Create `scripts/tests/test_vggt_feat_cuesoft_gate_contract.py` that asserts the trainer source contains these exact tokens:
- `cue_soft`
- `_get_pseudo_mask_batch(`
- `Pseudo mask NPZ is required for vggt_feat_gating='cue_soft'`
- `gating='cue_soft' requested but pseudo masks are unavailable`
- `weight_map = cue_mask if weight_map is None else (weight_map * cue_mask)`

Implementation note:
- this is a source contract test, not a heavy runtime trainer test;
- it should read `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` and assert these tokens exist.

**Step 2: Extend existing flag/passthrough contract tests**

Update these tests so they require:

1. `scripts/tests/test_vggt_feature_loss_flags.py`
   - `cue_soft`
   - `pseudo_mask_npz`
   - `vggt_feat_gating`

2. `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`
   - `--pseudo-mask-npz`
   - `--pseudo-mask-end-step`
   - `PSEUDO_MASK_NPZ`
   - `PSEUDO_MASK_END_STEP`
   - `cue_soft`

3. `scripts/tests/test_runner_args_passthrough.py`
   - assert the base runner forwards `--pseudo-mask-npz`
   - assert the base runner forwards `--pseudo-mask-end-step`
   - assert the env-driven path value appears in trainer args

**Step 3: Run the new/updated tests to make sure they fail first**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_feat_cuesoft_gate_contract.py \
  scripts/tests/test_vggt_feature_loss_flags.py \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py -q
```

Expected: FAIL because `cue_soft` and pseudo-mask passthrough are not implemented yet.

---

### Task 3: Implement `cue_soft` gating in the trainer without touching loss geometry

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Test: `scripts/tests/test_vggt_feat_cuesoft_gate_contract.py`
- Test: `scripts/tests/test_vggt_feature_loss_flags.py`

**Step 1: Extend gating validation**

Allow `vggt_feat_gating` to accept:
- `none`
- `framediff`
- `cue`
- `cue_soft`

Keep `cue` untouched for historical audit compatibility; do not silently rename it.

**Step 2: Make pseudo masks loadable for `cue_soft` even when weak fusion is disabled**

In `_maybe_load_pseudo_masks`, add a third enable condition conceptually equivalent to:

```python
feat_cue_enabled = (
    float(cfg.lambda_vggt_feat) > 0.0
    and str(cfg.vggt_feat_gating).strip().lower() == "cue_soft"
)
```

Then only early-return when **all** of these are false:
- weak fusion disabled
- corr gate disabled
- feat cue disabled

Required behavior:
- if `cue_soft` is requested and `pseudo_mask_npz` is empty, raise a clear `ValueError` containing:
  - `Pseudo mask NPZ is required for vggt_feat_gating='cue_soft'`
- if `cue_soft` is requested and the NPZ file path does not exist, raise `FileNotFoundError`

**Step 3: Add the new `cue_soft` branch in `_compute_vggt_feature_loss`**

Add an `elif` branch for:

```python
elif gating_mode == "cue_soft":
```

Required implementation details:
- fetch the cue map via:
  - `self._get_pseudo_mask_batch(frame_idx=data["frame_idx"], camera_idx=data["camera_idx"], height=int(self.vggt_feat_phi_size[0]), width=int(self.vggt_feat_phi_size[1]))`
- if cue map is `None`, print one warning containing:
  - `gating='cue_soft' requested but pseudo masks are unavailable`
  - then fall back to `none`
- otherwise:
  - clamp cue map to `[0,1]`
  - do **not** apply `_top_p_mask`
  - do **not** binarize it
  - combine it with any confidence map multiplicatively:
    - `weight_map = cue_mask if weight_map is None else (weight_map * cue_mask)`

**Step 4: Add one diagnostic scalar for cue intensity**

Where feature-loss scalars are written, add one extra scalar when `cue_soft` is active:
- `vggt_feat/cue_mean`

Log the per-step mean of the cue weight map actually used by the feature-loss branch.

**Step 5: Run the focused trainer contract set**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_feat_cuesoft_gate_contract.py \
  scripts/tests/test_vggt_feature_loss_flags.py -q
```

Expected: PASS.

---

### Task 4: Extend the base SelfCap feature-loss runner so `cue_soft` is actually configurable

**Files:**
- Modify: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
- Test: `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`
- Test: `scripts/tests/test_runner_args_passthrough.py`

**Step 1: Add pseudo-mask env knobs to the base runner**

Add these env-configurable vars near the other feature-loss settings:
- `PSEUDO_MASK_NPZ="${PSEUDO_MASK_NPZ:-}"`
- `PSEUDO_MASK_END_STEP="${PSEUDO_MASK_END_STEP:-0}"`
- `PSEUDO_MASK_WEIGHT="${PSEUDO_MASK_WEIGHT:-0}"`

Important scope rule:
- this route uses pseudo masks only for `cue_soft` feature gating;
- it must **not** accidentally enable weak fusion weighting unless explicitly requested later.

**Step 2: Add a runner-side validation for `cue_soft`**

Before launching the trainer:
- if `VGGT_FEAT_GATING=cue_soft` and `PSEUDO_MASK_NPZ` is empty, exit non-zero with a clear error;
- if `VGGT_FEAT_GATING=cue_soft` and `PSEUDO_MASK_NPZ` path is missing, exit non-zero with a clear error.

**Step 3: Pass the pseudo-mask flags through to the trainer**

Add these CLI flags to the trainer command:
- `--pseudo-mask-npz "$PSEUDO_MASK_NPZ"`
- `--pseudo-mask-end-step "$PSEUDO_MASK_END_STEP"`
- `--pseudo-mask-weight "$PSEUDO_MASK_WEIGHT"`

Also extend the startup echo so it prints:
- `pseudo_mask_npz`
- `pseudo_mask_end_step`
- `pseudo_mask_weight`

**Step 4: Run the base-runner focused tests**

Run:
```bash
pytest -q \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py -q
```

Expected: PASS.

---

### Task 5: Add a dedicated paired rerun runner and a route-specific summarizer

**Files:**
- Create: `scripts/run_planb_feat_v2_cuesoft400_pair.sh`
- Create: `scripts/summarize_vggt_cuesoft_pair.py`
- Create: `scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py`
- Create: `scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py`

**Step 1: Write the runner contract test first**

Create `scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py` that asserts the new runner contains these exact tokens:
- `MAX_STEPS=400`
- `SEEDS=42,43`
- `LAMBDA_VGGT_FEAT=0`
- `LAMBDA_VGGT_FEAT=0.005`
- `VGGT_FEAT_LOSS_TYPE=cosine`
- `VGGT_FEAT_GATING=cue_soft`
- `VGGT_FEAT_START_STEP=150`
- `VGGT_FEAT_RAMP_STEPS=150`
- `VGGT_FEAT_EVERY=16`
- `PSEUDO_MASK_WEIGHT=0`
- `PSEUDO_MASK_END_STEP=0`
- `pseudo_masks_dyn_q0p95_scaled.npz`
- `control_novggt`
- `cuesoft_vggtprobe_q0p95`
- `EVAL_STEPS=199,399`
- `SAVE_STEPS=199,399`

**Step 2: Write the summarizer contract test first**

Create `scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py` that asserts the summarizer source contains these exact tokens:
- `test_step0199.json`
- `test_step0198.json`
- `test_step0399.json`
- `test_step0398.json`
- `delta_psnr`
- `delta_lpips`
- `delta_tlpips`
- `both_seeds_tlpips_negative_399`

**Step 3: Run the two new tests and confirm they fail first**

Run:
```bash
pytest -q \
  scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py \
  scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py -q
```

Expected: FAIL because the runner and summarizer do not exist yet.

**Step 4: Implement the paired runner**

Create `scripts/run_planb_feat_v2_cuesoft400_pair.sh` with these fixed settings:
- output root:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/`
- cue source:
  - `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/pseudo_masks_dyn_q0p95_scaled.npz` (generated inside the new worktree)
- shared external inputs:
  - `DATA_DIR=$MAIN_REPO_ROOT/data/selfcap_bar_8cam60f`
  - `VGGT_FEAT_CACHE_NPZ=$MAIN_REPO_ROOT/outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
  - `BASELINE_INIT_NPZ=$MAIN_REPO_ROOT/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz`
  - `PLANB_INIT_NPZ=$MAIN_REPO_ROOT/outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- shared training knobs:
  - `MAX_STEPS=400`
  - `VGGT_FEAT_PHI_NAME=token_proj`
  - `VGGT_FEAT_PATCH_K=0`
  - `VGGT_FEAT_USE_CONF=1`
  - `VGGT_FEAT_START_STEP=150`
  - `VGGT_FEAT_RAMP_STEPS=150`
  - `VGGT_FEAT_EVERY=16`
  - `EVAL_STEPS=199,399`
  - `SAVE_STEPS=199,399`

Per-seed arms:
1. **control**
   - `result_name=seed${seed}_control_novggt`
   - `LAMBDA_VGGT_FEAT=0`
   - `VGGT_FEAT_LOSS_TYPE=cosine`
   - `VGGT_FEAT_GATING=none`
   - `PSEUDO_MASK_WEIGHT=0`
   - `PSEUDO_MASK_END_STEP=0`

2. **treatment**
   - `result_name=seed${seed}_cuesoft_vggtprobe_q0p95`
   - `LAMBDA_VGGT_FEAT=0.005`
   - `VGGT_FEAT_LOSS_TYPE=cosine`
   - `VGGT_FEAT_GATING=cue_soft`
   - `PSEUDO_MASK_NPZ=<scaled cue npz>`
   - `PSEUDO_MASK_WEIGHT=0`
   - `PSEUDO_MASK_END_STEP=0`

Required safety behavior:
- if `MAIN_REPO_ROOT` is empty, fail loudly and ask the operator to re-export it from Task 0;
- if target result dir already contains `stats/test_step0398.json` or `stats/test_step0399.json`, fail loudly and exit non-zero;
- print one startup line containing `seed`, `arm`, `result_dir`, `gating`, `lambda`, `cue_npz`, `data_dir`, `cache_npz`, `planb_init_npz`.

**Step 5: Implement the summarizer**

Create `scripts/summarize_vggt_cuesoft_pair.py` that:
- loads paired control/treatment stats for `step199` and `step399` using candidate filenames `0199/0198` and `0399/0398`;
- writes:
  - `summary.json`
  - `per_seed.csv`
- computes:
  - `mean_delta_psnr_399`
  - `mean_delta_lpips_399`
  - `mean_delta_tlpips_399`
  - `both_seeds_tlpips_negative_399`

**Step 6: Run the new runner/summarizer contract tests**

Run:
```bash
pytest -q \
  scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py \
  scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py -q
```

Expected: PASS.

---

### Task 6: Run the focused test pack before spending GPU

**Files:**
- Test: `scripts/tests/test_vggt_feat_cuesoft_gate_contract.py`
- Test: `scripts/tests/test_vggt_feature_loss_flags.py`
- Test: `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`
- Test: `scripts/tests/test_runner_args_passthrough.py`
- Test: `scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py`
- Test: `scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py`

**Step 1: Run the whole focused pack**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_feat_cuesoft_gate_contract.py \
  scripts/tests/test_vggt_feature_loss_flags.py \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py \
  scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py \
  scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py -q
```

Expected: PASS.

---

### Task 7: Run seed42 first, apply the unchanged early-stop rule, then decide whether to run seed43

**Files:**
- Modify: `notes/2026-03-07-vggt-cuesoft-go-nogo.md`
- Read: `scripts/run_planb_feat_v2_cuesoft400_pair.sh`
- Read: `scripts/summarize_vggt_cuesoft_pair.py`

**Step 1: Launch only seed42 first**

Run:
```bash
SEEDS=42 bash scripts/run_planb_feat_v2_cuesoft400_pair.sh
```

Expected: exactly two run dirs exist:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/seed42_control_novggt`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/seed42_cuesoft_vggtprobe_q0p95`

**Step 2: Summarize seed42 only**

Run:
```bash
"$VENV_PYTHON" scripts/summarize_vggt_cuesoft_pair.py \
  --root_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair \
  --seeds 42 \
  --treatment_suffix cuesoft_vggtprobe_q0p95 \
  --out_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/summary_seed42
```

Expected: `summary_seed42/summary.json` exists.

**Step 3: Apply the unchanged early-stop rule**

Use the same checkpoint logic as the previous minimal reruns:
- `ΔPSNR@199 < 0`
- `ΔLPIPS@199 > 0`
- `ΔtLPIPS@199 >= 0`

If all three are true:
- mark the route as `early-no-go`
- do not run `seed43`
- skip directly to Task 9 for final write-up

Otherwise:
- continue to Task 8

**Step 4: Update the note checkpoint section**

Add to the note:
- scaled cue source path
- seed42 checkpoint deltas
- whether early-stop triggered
- one sentence confirming this route changes **signal selection only**, not loss geometry

---

### Task 8: Finish the paired 400-step rerun and summarize the route-level outcome

**Files:**
- Modify: `notes/2026-03-07-vggt-cuesoft-go-nogo.md`

**Step 1: If early-stop did not trigger, run only the remaining seed**

Run:
```bash
SEEDS=43 bash scripts/run_planb_feat_v2_cuesoft400_pair.sh
```

Expected: four run dirs exist in total:
- `seed42_control_novggt`
- `seed42_cuesoft_vggtprobe_q0p95`
- `seed43_control_novggt`
- `seed43_cuesoft_vggtprobe_q0p95`

**Step 2: Generate the final summary packet**

Run:
```bash
"$VENV_PYTHON" scripts/summarize_vggt_cuesoft_pair.py \
  --root_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair \
  --seeds 42,43 \
  --treatment_suffix cuesoft_vggtprobe_q0p95 \
  --out_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/summary
```

Expected: both files exist:
- `summary/summary.json`
- `summary/per_seed.csv`

**Step 3: Update the note with the final evidence block**

The note must include:
- one compact table for `seed42/43 × step199/399`
- summary lines for:
  - `mean ΔPSNR@399`
  - `mean ΔLPIPS@399`
  - `mean ΔtLPIPS@399`
  - `both_seeds_tlpips_negative_399`
- one paragraph comparing this route against:
  - `final knife`
  - `local-softmatch loss-fix rerun`

**Step 4: Verify the run artifacts exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/summary/summary.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_cuesoft400_pair/summary/per_seed.csv'),
    Path('notes/2026-03-07-vggt-cuesoft-go-nogo.md'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 9: Apply the go/no-go rule and close or retain this single route

**Files:**
- Modify: `notes/2026-03-07-vggt-cuesoft-go-nogo.md`

**Step 1: Apply the same final decision rule**

Use the final `step399` summary and threshold `0.001371`.

**GO (worth at most one later replication):**
- `mean ΔtLPIPS@399 <= -0.001371`
- `mean ΔLPIPS@399 <= 0`
- `mean ΔPSNR@399 >= 0`
- both seeds satisfy `ΔtLPIPS@399 < 0`

**STOP (default):**
- anything else
- including early-stop
- including any mixed pattern like `PSNR` up but `LPIPS/tLPIPS` not cleanly improved
- including `LPIPS` slightly better but `PSNR` negative or `tLPIPS` still within noise band

**Step 2: Add one explicit route-level interpretation rule**

The note must say:
- if this rerun is `STOP`, then current `SelfCap cue-soft route` is closed for this project;
- if this rerun is `GO`, that only earns **one later replication**, not immediate promotion to thesis mainline.

**Step 3: Write the final verdict line into the note**

The note must contain exactly one of:
- `Final verdict: GO (cue-soft rerun is positive enough for one later replication, not thesis mainline)`
- `Final verdict: STOP (cue-soft rerun does not justify further reopen)`

Also include:
- one `Boundary:` sentence
- one sentence containing `thesis mainline`
- one sentence explicitly answering whether this route was a better bet than `local-softmatch loss-fix`

---

### Task 10: Final validation and handoff check

**Files:**
- Read: `notes/2026-03-07-vggt-cuesoft-go-nogo.md`

**Step 1: Re-run the focused pytest pack**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_feat_cuesoft_gate_contract.py \
  scripts/tests/test_vggt_feature_loss_flags.py \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py \
  scripts/tests/test_run_planb_feat_v2_cuesoft400_pair_contract.py \
  scripts/tests/test_summarize_vggt_cuesoft_pair_contract.py -q
```

Expected: PASS.

**Step 2: Run a no-overclaim text check**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('notes/2026-03-07-vggt-cuesoft-go-nogo.md').read_text(encoding='utf-8')
assert 'thesis mainline' in text
assert 'Boundary:' in text
for bad in ['稳定全面优于', '已证明 VGGT 优化桥成立', '彻底证明原版开题全部完成']:
    assert bad not in text, bad
print('ok')
PY
```

Expected: prints `ok`.

**Step 3: Re-answer the single route question**

After all artifacts exist, you must be able to answer in one sentence:

```text
如果把 stage-2 VGGT feature loss 的选区改成 VGGT cue-backed dense soft weighting，而不是 framediff hard top-p，这条 route 在 SelfCap 上还值得继续投入吗？
```

Expected:
- if `GO`, answer `值得保留一次后续 replication，但不进入 thesis mainline`;
- if `STOP`, answer `不值得继续投入，当前 SelfCap cue-soft route 在本项目内关闭`.
