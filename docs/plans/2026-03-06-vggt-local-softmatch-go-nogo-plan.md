# VGGT Local Soft-Matching Go/No-Go Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用一次最小、受控、可停止的 `local-window / soft matching feature loss` 重开实验，回答“把严格同-cell `token_proj cosine loss` 换成局部窗口容忍匹配后，`VGGT -> 优化 -> 收益` 这条桥在 `SelfCap` 上是否终于出现可信正信号”。

**Architecture:** 本计划只允许一次“换损失假设”的最小重开，不再继续 `framediff top-p gate` 调参，也不再扩成开放式 sweep。实现上先在 trainer 中加入一个可单测的 `local-window softmin cosine` loss，再用 `SelfCap / seed42,43 / 400-step / no-extra-loss vs local-softmatch` 做配对对照，并用预注册门槛直接判定 `go` 或 `stop`。

**Tech Stack:** PyTorch trainer under `third_party/FreeTimeGsVanilla/`, Bash runners in `scripts/`, `pytest`, Markdown notes under `notes/`, existing `protocol_v2` stats JSON / report-pack docs.

---

## Scope guardrails

- 只重开 **这一条** 路线：`local-window / soft matching feature loss`。
- 不继续 `framediff-gated token_proj cosine loss` 的任何超参扫。
- 不同时重开 `correspondence-backed gate`、`soft weighting framediff` 或其他备选路线。
- 数据集固定为 `SelfCap`；seed 固定为 `42,43`；训练窗口固定为 `400-step`。
- 对照组固定为 `no extra VGGT optimization loss`，不是旧 `framediff` recipe。
- 处理组固定为：`token_proj + local softmin cosine + gating=none + lambda=0.005 + start=150 + ramp=150 + every=16`。
- 成败判定继续用现有 `tLPIPS` 噪声带阈值：`0.001371`。
- `outputs/` 仅新增 append-only 目录；不得手改历史结果。
- 本轮默认 **不提交 git commit**；只产出代码、结果和文档。

## Execution map

- **代码阶段**：只改 1 个 trainer、1 个 helper、2 个 runner、4 个测试/总结脚本、2 个文档。
- **最小运行预算**：如果 `seed42 @ step199` 触发早停，只跑 2 个 run 目录。
- **最大运行预算**：如果未触发早停，总共跑 4 个 run 目录：`2 seeds × 2 arms`。
- **结果目录固定**：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/`。
- **delta 口径固定**：始终用 `treatment - control`，且只读 `stats/test_step0199.json` 与 `stats/test_step0399.json` 中的 `psnr`、`lpips`、`tlpips`。
- **路由结论只有两档**：`GO (minimal positive reopen, not thesis mainline)` 或 `STOP (route does not justify further reopen)`。

## Implementation notes before touching code

- trainer 入口由 `tyro` 从 dataclass 自动暴露 CLI 参数，因此新增 `vggt_feat_local_radius` / `vggt_feat_local_softmin_tau` 时，**不需要额外改 argparse 文件**；重点是 dataclass、校验逻辑、loss 分支和 runner 透传。
- 新增 helper 建议命名为 `compute_local_softmin_cosine_loss_map`，放在 `third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py`，保持纯函数、无副作用、无随机性。
- `radius=0` 必须退化为严格 same-cell cosine loss；这既是正确性要求，也是后续 debug 时最重要的 sanity check。
- 第一轮 treatment **不再使用任何 gate**；`VGGT_FEAT_GATING=none` 是本次“换损失假设、先不换 signal source”的关键边界。
- 配对 runner 必须对已有结果目录保持保守：若目标目录中已存在 `stats/test_step0399.json`，直接报错退出，要求换新目录标签，避免污染 append-only 产物。
- 最终 note、brief 和 alignment 只能保守更新，不允许把本轮结果写成“已证明 VGGT 优化桥成立”。

---

### Task 0: Create isolated worktree and freeze the question

**Files:**
- Read: `AGENTS.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-final-knife/notes/2026-03-06-final-knife-vggt-closed-loop.md`
- Read: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`

**Step 1: Create and enter a dedicated worktree**

Run:
```bash
export MAIN_REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$MAIN_REPO_ROOT"
git worktree add .worktrees/owner-b-20260306-vggt-softmatch -b feat/vggt-softmatch-go-nogo
cd .worktrees/owner-b-20260306-vggt-softmatch
pwd
```

Expected: all following work happens inside `.worktrees/owner-b-20260306-vggt-softmatch`.

**Step 2: Pin the shared Python environment**

Run:
```bash
export VENV_PYTHON="${VENV_PYTHON:-$MAIN_REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
[ -x "$VENV_PYTHON" ]
```

Expected: the shared interpreter is executable from the worktree.

**Step 3: Verify the four evidence anchors before reopening**

Run:
```bash
[ -f docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md ]
[ -f docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md ]
[ -f "$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-final-knife/notes/2026-03-06-final-knife-vggt-closed-loop.md" ]
[ -f scripts/run_train_planb_feature_loss_v2_selfcap.sh ]
```

Expected: all files exist; this confirms the reopen is grounded in the already closed evidence chain.

**Step 4: Freeze the one-sentence objective in the work log**

Write this sentence into the execution log before coding:

```text
本轮只回答一个问题：把严格同-cell 的 token_proj cosine loss 换成 local-window soft matching 后，VGGT 优化桥是否在 SelfCap 上出现超出噪声带的最小正信号。
```

Expected: no scope creep into second-choice routes.

---

### Task 1: Add a local-window soft-matching loss primitive with real unit tests

**Files:**
- Create: `third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py`
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Create: `scripts/tests/test_vggt_local_softmatch_loss.py`
- Modify: `scripts/tests/test_vggt_feature_loss_flags.py`

**Step 1: Write the failing unit test first**

Create `scripts/tests/test_vggt_local_softmatch_loss.py` with two deterministic synthetic cases:

1. **zero-shift sanity case**
   - `phi_render == phi_gt`
   - call `compute_local_softmin_cosine_loss_map(..., radius=0, tau=0.10)`
   - assert mean loss is numerically near zero.

2. **one-cell shift tolerance case**
   - `phi_gt` is a 1-cell shifted version of `phi_render`
   - compute both:
     - strict same-cell cosine loss
     - new local-window soft-matching cosine loss with radius `1`
   - assert the new local-window loss is strictly smaller by a clear margin.

Recommended assertion sketch:
```python
assert local_loss.item() < strict_loss.item() - 0.10
assert local_loss.item() < 0.05
```

Implementation note for the test:
- avoid symmetric all-zero / one-hot toy data that can accidentally make multiple neighbors equally optimal;
- prefer a simple 2-channel gradient-style tensor so the 1-cell shift is unambiguous.

**Step 2: Run the test to confirm it fails first**

Run:
```bash
pytest -q scripts/tests/test_vggt_local_softmatch_loss.py -q
```

Expected: FAIL because the helper module does not exist yet.

**Step 3: Implement the smallest testable helper**

Create `third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py` with a pure function named exactly:

```python
compute_local_softmin_cosine_loss_map(
    phi_render: torch.Tensor,
    phi_gt: torch.Tensor,
    radius: int,
    tau: float,
) -> torch.Tensor
```

Function contract:
- input shapes are `[B,C,H,W]` and `[B,C,H,W]`;
- return shape is `[B,1,H,W]`;
- normalize both tensors on channel dim;
- build local GT neighborhoods with `torch.nn.functional.unfold` over `(2r+1)x(2r+1)` using `padding=radius` so output spatial size stays `H×W`;
- compute per-neighbor cosine loss `1 - cos(render, gt_neighbor)`;
- reduce neighborhood by differentiable softmin:
  - `softmin(losses, tau) = -tau * logsumexp(-losses / tau)`;
- reshape back to `[B,1,H,W]`.

Hard requirements:
- `radius=0` degenerates to same-cell cosine loss;
- `tau > 0`; invalid values fail loudly with `ValueError`;
- `radius >= 0`; invalid values fail loudly with `ValueError`;
- no random sampling, no masking, no file I/O inside the helper.

**Step 4: Wire the helper into the trainer**

Modify `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` in these three places:

1. **Config dataclass**
   - extend `vggt_feat_loss_type` allowed values to include `local_softmin_cosine`
   - add:
   ```python
   vggt_feat_local_radius: int = 0
   vggt_feat_local_softmin_tau: float = 0.10
   ```

2. **Validation in `_maybe_load_vggt_feat_cache`**
   - allow `local_softmin_cosine`
   - validate `vggt_feat_local_radius >= 0`
   - validate `vggt_feat_local_softmin_tau > 0`

3. **Loss branch in `_compute_vggt_feature_loss`**
   - when `cfg.vggt_feat_loss_type == "local_softmin_cosine"`, call the new helper to produce `loss_map`
   - keep existing confidence weighting, `patch_k` sampling, and later weighted averaging logic unchanged
   - do not alter `gating=framediff` implementation in this task; this route uses `gating=none`

Important note:
- because the script uses `tyro`, once these dataclass fields exist, the CLI flags become `--vggt-feat-local-radius` and `--vggt-feat-local-softmin-tau` automatically; do not waste time editing a separate parser file.

**Step 5: Extend the token-presence contract test**

Update `scripts/tests/test_vggt_feature_loss_flags.py` so the required tokens also include:
- `local_softmin_cosine`
- `vggt_feat_local_radius`
- `vggt_feat_local_softmin_tau`
- `compute_local_softmin_cosine_loss_map`

**Step 6: Run the focused validation set**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_local_softmatch_loss.py \
  scripts/tests/test_vggt_feature_loss_flags.py -q
```

Expected: PASS.

---

### Task 2: Expose the new knobs in the runner and add a paired go/no-go launcher

**Files:**
- Modify: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
- Modify: `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`
- Modify: `scripts/tests/test_runner_args_passthrough.py`
- Create: `scripts/run_planb_feat_v2_localsoftmatch400_pair.sh`
- Create: `scripts/tests/test_run_planb_feat_v2_localsoftmatch400_pair_contract.py`

**Step 1: Write the failing paired-runner contract test**

Create `scripts/tests/test_run_planb_feat_v2_localsoftmatch400_pair_contract.py` that asserts the new runner contains these exact tokens:
- `MAX_STEPS=400`
- `SEEDS=42,43`
- `LAMBDA_VGGT_FEAT=0`
- `LAMBDA_VGGT_FEAT=0.005`
- `VGGT_FEAT_LOSS_TYPE=local_softmin_cosine`
- `VGGT_FEAT_GATING=none`
- `VGGT_FEAT_LOCAL_RADIUS=1`
- `VGGT_FEAT_LOCAL_SOFTMIN_TAU=0.10`
- `VGGT_FEAT_START_STEP=150`
- `VGGT_FEAT_RAMP_STEPS=150`
- `VGGT_FEAT_EVERY=16`
- `EVAL_STEPS=199,399`
- `SAVE_STEPS=199,399`
- `control_novggt`
- `localsoftmatch_r1_tau0p10`

**Step 2: Run the contract test to make sure it fails**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_localsoftmatch400_pair_contract.py -q
```

Expected: FAIL because the runner does not exist yet.

**Step 3: Update the base stage-2 runner to forward the new flags**

Modify `scripts/run_train_planb_feature_loss_v2_selfcap.sh` to add env defaults:
- `VGGT_FEAT_LOCAL_RADIUS="${VGGT_FEAT_LOCAL_RADIUS:-0}"`
- `VGGT_FEAT_LOCAL_SOFTMIN_TAU="${VGGT_FEAT_LOCAL_SOFTMIN_TAU:-0.10}"`

Then forward them into the trainer CLI:
- `--vggt-feat-local-radius "$VGGT_FEAT_LOCAL_RADIUS"`
- `--vggt-feat-local-softmin-tau "$VGGT_FEAT_LOCAL_SOFTMIN_TAU"`

Also print them in the startup log line next to `loss`, `lambda`, `gating`.

**Step 4: Extend the existing runner contracts**

Update `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py` so it expects the new flag tokens.

Update `scripts/tests/test_runner_args_passthrough.py` so the fake trainer invocation asserts the base runner forwards:
- `--vggt-feat-local-radius`
- `--vggt-feat-local-softmin-tau`

**Step 5: Implement the paired go/no-go runner**

Create `scripts/run_planb_feat_v2_localsoftmatch400_pair.sh` with these exact behaviors:
- `set -euo pipefail`
- default output root:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/`
- loop `SEEDS=42,43`
- for each seed run exactly two jobs:
  1. **control:** `LAMBDA_VGGT_FEAT=0`, result name `seed${seed}_control_novggt`
  2. **treatment:**
     - `LAMBDA_VGGT_FEAT=0.005`
     - `VGGT_FEAT_LOSS_TYPE=local_softmin_cosine`
     - `VGGT_FEAT_GATING=none`
     - `VGGT_FEAT_LOCAL_RADIUS=1`
     - `VGGT_FEAT_LOCAL_SOFTMIN_TAU=0.10`
     - result name `seed${seed}_localsoftmatch_r1_tau0p10`
- shared fixed defaults for both arms:
  - `MAX_STEPS=400`
  - `VGGT_FEAT_START_STEP=150`
  - `VGGT_FEAT_RAMP_STEPS=150`
  - `VGGT_FEAT_EVERY=16`
  - `EVAL_STEPS=199,399`
  - `SAVE_STEPS=199,399`
  - `VGGT_FEAT_PHI_NAME=token_proj`
  - `VGGT_FEAT_PATCH_K=0`
  - `VGGT_FEAT_USE_CONF=1`

Required safety behavior in the runner:
- before launching each arm, if target result dir already contains `stats/test_step0399.json`, print a clear error and exit non-zero;
- do not auto-delete or reuse old result dirs;
- print one line at start summarizing `seed`, `arm`, `result_dir`, `loss_type`, `lambda`, `radius`, `tau`.

**Step 6: Run the focused runner validation set**

Run:
```bash
pytest -q \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py \
  scripts/tests/test_run_planb_feat_v2_localsoftmatch400_pair_contract.py -q
```

Expected: PASS.

---

### Task 3: Add a deterministic pair summarizer for audit-friendly deltas

**Files:**
- Create: `scripts/summarize_vggt_localsoftmatch_pair.py`
- Create: `scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py`

**Step 1: Write the failing contract test**

Create `scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py` with a toy directory tree containing:
- `seed42_control_novggt/stats/test_step0199.json`
- `seed42_control_novggt/stats/test_step0399.json`
- `seed42_localsoftmatch_r1_tau0p10/stats/test_step0199.json`
- `seed42_localsoftmatch_r1_tau0p10/stats/test_step0399.json`
- same for `seed43`

Toy JSON must use the real metric keys:
```json
{"psnr": 12.3, "lpips": 0.45, "tlpips": 0.08}
```

The test must assert the script writes:
- `summary.json`
- `per_seed.csv`

And that `summary.json` includes at least these keys:
```python
{
    "seeds",
    "step199",
    "step399",
    "mean_delta_psnr_399",
    "mean_delta_lpips_399",
    "mean_delta_tlpips_399",
    "both_seeds_tlpips_negative_399",
}
```

**Step 2: Run the test to verify it fails**

Run:
```bash
pytest -q scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py -q
```

Expected: FAIL because the script does not exist yet.

**Step 3: Implement the summarizer**

Create `scripts/summarize_vggt_localsoftmatch_pair.py` with inputs:
- `--root_dir`
- `--seeds 42,43`
- `--control_suffix control_novggt`
- `--treatment_suffix localsoftmatch_r1_tau0p10`
- `--out_dir`

Behavior:
- read `test_step0199.json` and `test_step0399.json` for each seed and each arm;
- fail loudly if any file is missing;
- fail loudly if any JSON misses `psnr`, `lpips`, or `tlpips`;
- compute deltas as `treatment - control` for:
  - `psnr`
  - `lpips`
  - `tlpips`
- write a row per seed × step into `per_seed.csv`;
- write `summary.json` with deterministic ordering and this exact shape:
```json
{
  "seeds": [42, 43],
  "step199": {
    "42": {"delta_psnr": 0.0, "delta_lpips": 0.0, "delta_tlpips": 0.0},
    "43": {"delta_psnr": 0.0, "delta_lpips": 0.0, "delta_tlpips": 0.0}
  },
  "step399": {
    "42": {"delta_psnr": 0.0, "delta_lpips": 0.0, "delta_tlpips": 0.0},
    "43": {"delta_psnr": 0.0, "delta_lpips": 0.0, "delta_tlpips": 0.0}
  },
  "mean_delta_psnr_399": 0.0,
  "mean_delta_lpips_399": 0.0,
  "mean_delta_tlpips_399": 0.0,
  "both_seeds_tlpips_negative_399": false
}
```

Do **not** bake the final verdict into this script; it should stay a pure summarizer.

**Step 4: Run the summarizer test**

Run:
```bash
pytest -q scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py -q
```

Expected: PASS.

---

### Task 4: Run the first causal checkpoint on `seed42 @ step199`

**Files:**
- Create: `notes/2026-03-06-vggt-local-softmatch-go-nogo.md`
- Read: `scripts/run_planb_feat_v2_localsoftmatch400_pair.sh`
- Read: `scripts/summarize_vggt_localsoftmatch_pair.py`

**Step 1: Launch only seed42 first**

Run:
```bash
SEEDS=42 bash scripts/run_planb_feat_v2_localsoftmatch400_pair.sh
```

Expected: exactly two run dirs exist:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/seed42_control_novggt`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/seed42_localsoftmatch_r1_tau0p10`

**Step 2: Summarize the seed42 checkpoint**

Run:
```bash
"$VENV_PYTHON" scripts/summarize_vggt_localsoftmatch_pair.py \
  --root_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair \
  --seeds 42 \
  --out_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary_seed42
```

Expected: `summary_seed42/summary.json` exists and contains `step199` / `step399` for seed42.

**Step 3: Apply the early stop rule at `step199`**

Read `summary_seed42/summary.json` and compute whether **all three** are true at `step199`:
- `ΔPSNR < 0`
- `ΔLPIPS > 0`
- `ΔtLPIPS >= 0`

Use this exact helper snippet if you want to avoid manual reading:
```bash
python3 - <<'PY'
import json
from pathlib import Path
obj = json.loads(Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary_seed42/summary.json').read_text())
d = obj['step199']['42']
stop = d['delta_psnr'] < 0 and d['delta_lpips'] > 0 and d['delta_tlpips'] >= 0
print({'delta_psnr': d['delta_psnr'], 'delta_lpips': d['delta_lpips'], 'delta_tlpips': d['delta_tlpips'], 'early_stop': stop})
PY
```

If all three are true:
- mark the route as `early-no-go`;
- do **not** run `seed43`;
- skip directly to Task 6 for final write-up.

Otherwise:
- continue to Task 5.

**Step 4: Record the checkpoint in the note**

Create `notes/2026-03-06-vggt-local-softmatch-go-nogo.md` with these mandatory sections:
- `Question`
- `Exact config`
- `Seed42 step199 checkpoint`
- `Stop rule`
- `Current status`

The note must explicitly say:
- this is a **single reopening route**, not a new sweep;
- control is `no extra VGGT optimization loss`;
- treatment is `local-window soft matching` with `gating=none`;
- `seed43` only runs if the pre-registered early stop rule is not triggered.

---

### Task 5: Finish the paired 400-step go/no-go experiment

**Files:**
- Modify: `notes/2026-03-06-vggt-local-softmatch-go-nogo.md`

**Step 1: If the early stop rule did not trigger, run the full paired seeds**

Run:
```bash
SEEDS=42,43 bash scripts/run_planb_feat_v2_localsoftmatch400_pair.sh
```

Expected: four run dirs exist in total:
- `seed42_control_novggt`
- `seed42_localsoftmatch_r1_tau0p10`
- `seed43_control_novggt`
- `seed43_localsoftmatch_r1_tau0p10`

**Step 2: Generate the final summary packet**

Run:
```bash
"$VENV_PYTHON" scripts/summarize_vggt_localsoftmatch_pair.py \
  --root_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair \
  --seeds 42,43 \
  --out_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary
```

Expected: both files exist:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary/summary.json`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary/per_seed.csv`

**Step 3: Write the per-seed and mean deltas into the note**

Update `notes/2026-03-06-vggt-local-softmatch-go-nogo.md` with:
- one compact table for seed42 / seed43 at `step199` and `step399`
- one summary block containing:
  - `mean ΔPSNR@399`
  - `mean ΔLPIPS@399`
  - `mean ΔtLPIPS@399`
  - `both_seeds_tlpips_negative_399`
- one short paragraph explaining whether the final pattern is `clean positive`, `mixed`, or `early-no-go`

**Step 4: Verify the run artifacts exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/seed42_control_novggt/stats/test_step0399.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/seed42_localsoftmatch_r1_tau0p10/stats/test_step0399.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/seed43_control_novggt/stats/test_step0399.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/seed43_localsoftmatch_r1_tau0p10/stats/test_step0399.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary/summary.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary/per_seed.csv'),
    Path('notes/2026-03-06-vggt-local-softmatch-go-nogo.md'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

If Task 4 already early-stopped, replace this existence check with a smaller check that only requires the two `seed42` run dirs, `summary_seed42/summary.json`, and the note.

---

### Task 6: Apply the pre-registered go/no-go rule and update the discussion docs

**Files:**
- Modify: `notes/2026-03-06-vggt-local-softmatch-go-nogo.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Apply the fixed decision rule**

Use the final `step399` summary and the noise-band threshold `0.001371`.

**GO (worth one later replication, but still not mainline):**
- `mean ΔtLPIPS@399 <= -0.001371`
- `mean ΔLPIPS@399 <= 0`
- `mean ΔPSNR@399 >= 0`
- both seeds satisfy `ΔtLPIPS@399 < 0`

**STOP (default):**
- anything else
- including any `mixed` pattern like `PSNR` up but `LPIPS/tLPIPS` not cleanly improved
- including the `early-no-go` case where only `seed42` was run and already failed the checkpoint rule

**Step 2: Write the verdict into the note**

The note must contain exactly one of these verdict lines:
- `Final verdict: GO (minimal positive reopen, not thesis mainline)`
- `Final verdict: STOP (local-softmatch route does not justify further reopen)`

It must also contain:
- one explicit boundary sentence beginning with `Boundary:`
- one explicit thesis-position sentence containing `thesis mainline`

**Step 3: Update the single-file discussion brief conservatively**

Modify `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md` by adding one short dated subsection that records:
- this local-softmatch route was the **only** allowed reopen;
- exact experimental shape: `SelfCap / seed42,43 / 400-step / control=no-extra-loss / treatment=local-softmatch`;
- if early-stop happened, say so explicitly;
- the final verdict;
- one sentence on what the result does **not** prove.

**Step 4: Update the alignment table without inflating the claim**

Modify `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md` conservatively:
- keep the route-level story honest;
- append the new note path under the relevant `VGGT soft-prior 注入后的 stage-2 训练闭环` row;
- do **not** upgrade the row to `Done`.

If verdict is `STOP`, keep status as `Partial`.
If verdict is `GO`, status may remain `Partial` with an added phrase like `+ minimal positive reopen evidence`, but still **not** `Done`.

---

### Task 7: Final validation and handoff check

**Files:**
- Read: `notes/2026-03-06-vggt-local-softmatch-go-nogo.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Run the focused test pack**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_local_softmatch_loss.py \
  scripts/tests/test_vggt_feature_loss_flags.py \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py \
  scripts/tests/test_run_planb_feat_v2_localsoftmatch400_pair_contract.py \
  scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py -q
```

Expected: PASS.

**Step 2: Run a no-overclaim text check**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('notes/2026-03-06-vggt-local-softmatch-go-nogo.md').read_text(encoding='utf-8')
assert 'thesis mainline' in text
assert 'Boundary:' in text
for bad in ['稳定全面优于', '已证明 VGGT 优化桥成立', '彻底证明原版开题全部完成']:
    assert bad not in text, bad
print('ok')
PY
```

Expected: prints `ok`.

**Step 3: Run a deliverables existence check**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('docs/plans/2026-03-06-vggt-local-softmatch-go-nogo-plan.md'),
    Path('notes/2026-03-06-vggt-local-softmatch-go-nogo.md'),
    Path('docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md'),
    Path('docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

**Step 4: Re-answer the single decision question**

After all artifacts exist, you must be able to answer in one sentence:

```text
local-window / soft matching 这条一次性重开路线，在 SelfCap 两个 seed 的 400-step 受控对照里，是不是值得继续投入？
```

Expected:
- if `GO`, answer `值得做一次更完整 replication，但不进入 thesis mainline`;
- if `STOP`, answer `不值得继续投入，VGGT 方向在本项目里保留为 soft-prior evidence branch`.

