# VGGT Local-Softmatch Loss-Fix Rerun Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 只修一次 `local-softmatch` 的损失定义偏置问题，在其余实验设置完全不变的前提下，做一轮最小公平复测，回答“上一次失败到底是路线本身无效，还是被当前 softmin 公式的目标偏置误伤”。

**Architecture:** 这不是第二条新路线，而是对已关闭 `local-softmatch` 路线做一次 **single-change rerun**。唯一允许改动的是把当前带负偏置的 `local_softmin_cosine` 纠正为一个 **center-anchored / non-negative** 的局部软匹配损失；数据集、seed、步数、schedule、gating、门槛全部保持不变，然后继续用 `SelfCap / seed42,43 / 400-step / control vs treatment` 做 go/no-go 判定。

**Tech Stack:** PyTorch trainer under `third_party/FreeTimeGsVanilla/`, Bash runners in `scripts/`, existing pair summarizer, `pytest`, Markdown notes under `notes/`, existing `protocol_v2` stats JSON / report-pack docs.

---

## Scope guardrails

- 这次只允许修 **一个问题**：`local_softmin_cosine` 的 loss 公式偏置。
- 不引入 `correspondence-backed gate`，不引入新 signal source，不改 schedule，不改数据集，不加新 seed。
- 仍然使用 `SelfCap`、`seed42,43`、`400-step`、`gating=none`、`lambda=0.005`、`start=150`、`ramp=150`、`every=16`。
- Control 仍是 `no extra VGGT optimization loss`，不是旧 framediff，也不是别的 stage-2 变体。
- 旧 `local_softmin_cosine` 实现与旧 note 必须保留，作为历史审计证据；新 rerun 必须使用 **新 loss type 名称**，不能覆盖旧结果口径。
- `outputs/` 只新增 append-only 目录；不得覆盖 `.worktrees/owner-b-20260306-vggt-softmatch/` 下的旧结果。
- 成败判定继续使用原门槛：`mean ΔtLPIPS@399 <= -0.001371`、`mean ΔLPIPS@399 <= 0`、`mean ΔPSNR@399 >= 0`、且两颗 seed 的 `ΔtLPIPS@399 < 0`。
- 如果这次 loss-fix rerun 仍然 `STOP`，则把 **current local-softmatch family** 在本项目内视为关闭，不再继续以“再修一点”为由重开。

## Root-cause hypothesis being tested

本计划只检验下面这个单一假设：

> 上一轮 `local-softmatch` 的 mixed 结果，有相当一部分来自当前 `softmin = -tau * logsumexp(-loss/tau)` 带来的目标偏置：它会在 `radius>0` 时产生负基线或局部平滑奖励，导致 treatment 更像“模糊化 regularizer”，而不是公平的局部匹配监督。

因此，这次 rerun 的目标不是“让方法更强”，而是先让它 **更公平、可解释、零基线明确**。

## Proposed formula correction

保留“local window + soft matching”这个大思路，但把 treatment 的 loss 公式改成一个 **center-anchored non-negative** 版本。

### New treatment loss definition

For each pixel / token location:

1. 计算邻域内所有候选的 cosine loss：`neighbor_losses`
2. 取中心位置的 loss：`center_loss`
3. 计算 soft weights：
   - `weights = softmax(-neighbor_losses / tau)`
4. 计算 soft candidate：
   - `soft_candidate = sum(weights * neighbor_losses)`
5. 最终 loss 定义为：
   - `loss = min(center_loss, soft_candidate)`
   - 实现时可写成 `torch.minimum(center_loss, soft_candidate)`

### Why this correction

这一定义的三个目标是：
- **non-negative**：loss 不应因为聚合公式本身变成负值；
- **center anchored**：如果中心位已经 perfect match（`center_loss=0`），则最终 loss 也必须是 `0`，不能再因为周围邻居而凭空奖励/惩罚；
- **still soft**：当附近位置比中心更合适时，仍允许通过软权重得到比中心更低的局部匹配代价。

### Explicit non-goals

- 这次不追求“最优局部匹配公式”；
- 这次不比较 hard-min / softmin / softavg 多种变体；
- 这次只做一个**最小纠偏版本**，用来验证“是不是旧公式本身误伤了路线判断”。

---

### Task 0: Create clean rerun worktree and freeze the fairness question

**Files:**
- Read: `AGENTS.md`
- Read: `docs/plans/2026-03-06-vggt-local-softmatch-go-nogo-plan.md`
- Read: `$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-vggt-softmatch/notes/2026-03-06-vggt-local-softmatch-go-nogo.md`
- Read: `$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-vggt-softmatch/third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py`
- Read: `$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-vggt-softmatch/outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary/summary.json`

**Step 1: Create and enter a dedicated rerun worktree**

Run:
```bash
export MAIN_REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$MAIN_REPO_ROOT"
git worktree add -b feat/vggt-softmatch-lossfix-rerun \
  .worktrees/owner-b-20260306-vggt-softmatch-lossfix \
  feat/vggt-softmatch-go-nogo
cd .worktrees/owner-b-20260306-vggt-softmatch-lossfix
pwd
```

Expected:
- new worktree is created from `feat/vggt-softmatch-go-nogo`, not from current repo root `HEAD`;
- all following work happens inside `.worktrees/owner-b-20260306-vggt-softmatch-lossfix`.

Why this matters:
- the prior `local-softmatch` implementation baseline does **not** exist in the main repo root;
- it only exists on `feat/vggt-softmatch-go-nogo` / the old worktree;
- creating this rerun worktree from the wrong base would silently drop the code being fairly rerun.

**Step 2: Pin the shared Python environment**

Run:
```bash
export VENV_PYTHON="${VENV_PYTHON:-$MAIN_REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
[ -x "$VENV_PYTHON" ]
```

Expected: the shared interpreter is executable from the new worktree.

**Step 3: Verify old local-softmatch evidence exists and stays untouched**

Run:
```bash
[ -f "$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-vggt-softmatch/notes/2026-03-06-vggt-local-softmatch-go-nogo.md" ]
[ -f "$MAIN_REPO_ROOT/.worktrees/owner-b-20260306-vggt-softmatch/outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatch400_pair/summary/summary.json" ]
```

Expected: old note and old summary both exist; this rerun is additive, not destructive.

**Step 4: Freeze the one-sentence fairness objective in the work log**

Write this sentence into the execution log before coding:

```text
本轮只回答一个问题：如果只修 local-softmatch 的 loss 公式偏置、其他设置完全不变，这条路线是否还会继续表现为 mixed / stop。
```

Expected: no drift into second-order method search.

---

### Task 1: Add a formula-corrected loss helper and prove its basic properties

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py`
- Create: `scripts/tests/test_vggt_local_softmatch_lossfix.py`
- Modify: `scripts/tests/test_vggt_feature_loss_flags.py`

**Step 1: Write the failing unit test first**

Create `scripts/tests/test_vggt_local_softmatch_lossfix.py` and test a **new** helper function named exactly:

```python
compute_local_centered_softmatch_cosine_loss_map
```

The test file must cover these three cases:

1. **radius=1, identical inputs, zero baseline**
   - build deterministic `phi_render == phi_gt`
   - call the new helper with `radius=1, tau=0.10`
   - assert mean loss is numerically near zero:
   ```python
   assert abs(loss_map.mean().item()) < 1e-6
   ```

2. **radius=1, identical inputs, non-negative everywhere**
   - use the same deterministic tensor
   - assert:
   ```python
   assert torch.all(loss_map >= -1e-8)
   ```

3. **one-cell shift tolerance vs strict same-cell**
   - construct a one-cell shifted `phi_gt`
   - compute strict same-cell cosine loss
   - compute new corrected local loss with `radius=1`
   - assert corrected local loss is strictly smaller than strict same-cell loss by a visible margin

Implementation note for the test:
- reuse the same style as the previous local-softmatch test; use a gradient / angle-based tensor, avoid degenerate symmetric patterns.

**Step 2: Run the test to make sure it fails first**

Run:
```bash
pytest -q scripts/tests/test_vggt_local_softmatch_lossfix.py -q
```

Expected: FAIL because the new helper does not exist yet.

**Step 3: Implement the corrected helper without deleting the old one**

Modify `third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py` to:
- keep existing `compute_local_softmin_cosine_loss_map` untouched for audit reproducibility;
- add a second helper named exactly:

```python
compute_local_centered_softmatch_cosine_loss_map(
    phi_render: torch.Tensor,
    phi_gt: torch.Tensor,
    radius: int,
    tau: float,
) -> torch.Tensor
```

Required implementation details:
- validate `radius >= 0`, `tau > 0`, rank-4 matching shapes;
- normalize on channel dim with `F.normalize(..., eps=1e-6)`;
- use `F.unfold(..., kernel_size=2*radius+1, padding=radius)` to extract GT neighborhoods;
- compute `neighbor_losses` as cosine losses for all candidates;
- identify the center candidate index as `(patch_side * patch_side) // 2`;
- compute:
  - `center_loss`
  - `weights = softmax(-neighbor_losses / tau, dim=1)`
  - `soft_candidate = (weights * neighbor_losses).sum(dim=1, keepdim=True)`
  - `loss = torch.minimum(center_loss, soft_candidate)`
- reshape to `[B,1,H,W]`;
- clamp final loss with `torch.clamp_min(loss, 0.0)` as a safety belt.

**Step 4: Extend the feature-loss token contract**

Update `scripts/tests/test_vggt_feature_loss_flags.py` so required tokens also include:
- `local_centered_softmatch_cosine`
- `compute_local_centered_softmatch_cosine_loss_map`

Keep the previous `local_softmin_cosine` token check too.

**Step 5: Run the focused helper validation set**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_local_softmatch_loss.py \
  scripts/tests/test_vggt_local_softmatch_lossfix.py \
  scripts/tests/test_vggt_feature_loss_flags.py -q
```

Expected: PASS.

---

### Task 2: Add a new trainer loss type for the corrected formula

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Test: `scripts/tests/test_vggt_feature_loss_flags.py`

**Step 1: Extend the dataclass loss-type enum**

Add one new allowed loss type string:

```python
local_centered_softmatch_cosine
```

Do not rename or remove the existing:
- `l1`
- `cosine`
- `local_softmin_cosine`

**Step 2: Extend validation in `_maybe_load_vggt_feat_cache`**

Allow all four strings:
- `l1`
- `cosine`
- `local_softmin_cosine`
- `local_centered_softmatch_cosine`

Do not change the existing radius/tau validation logic.

**Step 3: Add a new loss branch in `_compute_vggt_feature_loss`**

Add a new `elif` branch:

```python
elif cfg.vggt_feat_loss_type == "local_centered_softmatch_cosine":
```

And call the new helper with:
- `phi_render=phi_render`
- `phi_gt=phi_gt`
- `radius=int(cfg.vggt_feat_local_radius)`
- `tau=float(cfg.vggt_feat_local_softmin_tau)`

Do not change:
- confidence weighting logic
- `patch_k` logic
- weighted averaging logic after `loss_map`
- gating logic

**Step 4: Run the focused trainer-token validation**

Run:
```bash
pytest -q scripts/tests/test_vggt_feature_loss_flags.py -q
```

Expected: PASS.

---

### Task 3: Add a dedicated rerun paired runner with a new output root

**Files:**
- Create: `scripts/run_planb_feat_v2_localsoftmatchfix400_pair.sh`
- Create: `scripts/tests/test_run_planb_feat_v2_localsoftmatchfix400_pair_contract.py`
- Read: `scripts/run_planb_feat_v2_localsoftmatch400_pair.sh`
- Read: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`

**Step 1: Write the failing paired-runner contract test**

Create `scripts/tests/test_run_planb_feat_v2_localsoftmatchfix400_pair_contract.py` that asserts the new runner contains these exact tokens:
- `MAX_STEPS=400`
- `SEEDS=42,43`
- `LAMBDA_VGGT_FEAT=0`
- `LAMBDA_VGGT_FEAT=0.005`
- `VGGT_FEAT_LOSS_TYPE=local_centered_softmatch_cosine`
- `VGGT_FEAT_GATING=none`
- `VGGT_FEAT_LOCAL_RADIUS=1`
- `VGGT_FEAT_LOCAL_SOFTMIN_TAU=0.10`
- `VGGT_FEAT_START_STEP=150`
- `VGGT_FEAT_RAMP_STEPS=150`
- `VGGT_FEAT_EVERY=16`
- `EVAL_STEPS=199,399`
- `SAVE_STEPS=199,399`
- `control_novggt`
- `localsoftmatchfix_r1_tau0p10`

**Step 2: Run the contract test to confirm it fails**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_localsoftmatchfix400_pair_contract.py -q
```

Expected: FAIL because the runner does not exist yet.

**Step 3: Implement the rerun paired runner**

Create `scripts/run_planb_feat_v2_localsoftmatchfix400_pair.sh` by copying the previous pair-runner pattern, but with a **new output root**:

```bash
outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/
```

Per-seed arms:
1. **control**
   - `result_name=seed${seed}_control_novggt`
   - `LAMBDA_VGGT_FEAT=0`
   - `VGGT_FEAT_LOSS_TYPE=cosine`
   - `VGGT_FEAT_LOCAL_RADIUS=0`
   - `VGGT_FEAT_LOCAL_SOFTMIN_TAU=0.10`

2. **treatment**
   - `result_name=seed${seed}_localsoftmatchfix_r1_tau0p10`
   - `LAMBDA_VGGT_FEAT=0.005`
   - `VGGT_FEAT_LOSS_TYPE=local_centered_softmatch_cosine`
   - `VGGT_FEAT_GATING=none`
   - `VGGT_FEAT_LOCAL_RADIUS=1`
   - `VGGT_FEAT_LOCAL_SOFTMIN_TAU=0.10`

Shared fixed settings remain unchanged from the previous rerun shape:
- `MAX_STEPS=400`
- `VGGT_FEAT_START_STEP=150`
- `VGGT_FEAT_RAMP_STEPS=150`
- `VGGT_FEAT_EVERY=16`
- `EVAL_STEPS=199,399`
- `SAVE_STEPS=199,399`
- `VGGT_FEAT_PHI_NAME=token_proj`
- `VGGT_FEAT_PATCH_K=0`
- `VGGT_FEAT_USE_CONF=1`

Required safety behavior:
- if target result dir already contains `stats/test_step0398.json` or `stats/test_step0399.json`, fail loudly and exit non-zero;
- print one startup line containing `seed`, `arm`, `result_dir`, `loss_type`, `lambda`, `radius`, `tau`.

**Step 4: Run the paired-runner contract test**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_localsoftmatchfix400_pair_contract.py -q
```

Expected: PASS.

---

### Task 4: Reuse the existing summarizer with a new treatment suffix

**Files:**
- Read: `scripts/summarize_vggt_localsoftmatch_pair.py`
- Read: `scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py`

**Step 1: Verify the existing summarizer already supports custom suffixes**

Confirm that `scripts/summarize_vggt_localsoftmatch_pair.py` accepts:
- `--control_suffix`
- `--treatment_suffix`

Expected: no code changes needed if those flags already work.

**Step 2: Run the existing summarizer contract test unchanged**

Run:
```bash
pytest -q scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py -q
```

Expected: PASS.

If it fails because suffix handling is too rigid, then and only then modify the summarizer minimally and rerun the test.

---

### Task 5: Add one pre-training fairness sanity check

**Files:**
- Create: `scripts/tests/test_vggt_local_softmatch_lossfix_fairness_contract.py`
- Read: `third_party/FreeTimeGsVanilla/src/vggt_feature_loss_utils.py`

**Step 1: Write a tiny regression-style fairness test**

Create `scripts/tests/test_vggt_local_softmatch_lossfix_fairness_contract.py` that checks one deterministic tensor under `radius=1`:
- old helper: `compute_local_softmin_cosine_loss_map`
- new helper: `compute_local_centered_softmatch_cosine_loss_map`

Required assertions:
- new helper mean loss is `>= -1e-8`
- new helper mean loss on identical inputs is smaller than `1e-6`
- old helper and new helper are **not numerically identical** on the same identical-input tensor

The goal is not to prove the old helper always fails, but to prove the new helper has a different and fairer baseline property.

**Step 2: Run the fairness test to confirm it fails first**

Run:
```bash
pytest -q scripts/tests/test_vggt_local_softmatch_lossfix_fairness_contract.py -q
```

Expected: FAIL before the new helper exists, PASS after Task 1 is completed.

**Step 3: Run the full loss-formulation test pack**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_local_softmatch_loss.py \
  scripts/tests/test_vggt_local_softmatch_lossfix.py \
  scripts/tests/test_vggt_local_softmatch_lossfix_fairness_contract.py \
  scripts/tests/test_vggt_feature_loss_flags.py -q
```

Expected: PASS.

---

### Task 6: Run seed42 first and apply the same early-stop rule

**Files:**
- Create: `notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md`
- Read: `scripts/run_planb_feat_v2_localsoftmatchfix400_pair.sh`
- Read: `scripts/summarize_vggt_localsoftmatch_pair.py`

**Step 1: Launch only seed42 first**

Run:
```bash
SEEDS=42 bash scripts/run_planb_feat_v2_localsoftmatchfix400_pair.sh
```

Expected: exactly two run dirs exist:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/seed42_control_novggt`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/seed42_localsoftmatchfix_r1_tau0p10`

**Step 2: Summarize seed42 with the existing summarizer**

Run:
```bash
"$VENV_PYTHON" scripts/summarize_vggt_localsoftmatch_pair.py \
  --root_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair \
  --seeds 42 \
  --treatment_suffix localsoftmatchfix_r1_tau0p10 \
  --out_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/summary_seed42
```

Expected: `summary_seed42/summary.json` exists.

**Step 3: Apply the unchanged early-stop rule**

Use the same checkpoint logic as the previous rerun:
- `ΔPSNR@199 < 0`
- `ΔLPIPS@199 > 0`
- `ΔtLPIPS@199 >= 0`

If all three are true:
- mark the route as `early-no-go`
- do not run `seed43`
- skip to Task 8 for final write-up

Otherwise:
- continue to Task 7

**Step 4: Write the checkpoint note stub**

Create `notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md` with mandatory sections:
- `Question`
- `Why this rerun exists`
- `Exact config`
- `Loss formula change`
- `Seed42 step199 checkpoint`
- `Stop rule`
- `Current status`

The note must explicitly say:
- only the loss formula was changed
- all other knobs remained fixed
- this rerun is testing fairness of the previous route verdict, not opening a second method family

---

### Task 7: Finish the paired 400-step rerun

**Files:**
- Modify: `notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md`

**Step 1: If early-stop did not trigger, run only the remaining seed**

Run:
```bash
SEEDS=43 bash scripts/run_planb_feat_v2_localsoftmatchfix400_pair.sh
```

Expected: four run dirs exist in total after the second launch:
- `seed42_control_novggt`
- `seed42_localsoftmatchfix_r1_tau0p10`
- `seed43_control_novggt`
- `seed43_localsoftmatchfix_r1_tau0p10`

Why only `SEEDS=43` here:
- Task 6 already launched `seed42` for the checkpoint;
- the paired runner is required to fail loudly if a target result dir already contains `test_step0398.json` / `test_step0399.json`;
- rerunning `seed42` here would cause an avoidable collision and make the plan non-executable as written.

**Step 2: Generate the final summary packet**

Run:
```bash
"$VENV_PYTHON" scripts/summarize_vggt_localsoftmatch_pair.py \
  --root_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair \
  --seeds 42,43 \
  --treatment_suffix localsoftmatchfix_r1_tau0p10 \
  --out_dir outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/summary
```

Expected: both files exist:
- `summary/summary.json`
- `summary/per_seed.csv`

**Step 3: Write the final per-seed and mean deltas into the note**

Update `notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md` with:
- one compact table for `seed42/43 × step199/399`
- summary lines for:
  - `mean ΔPSNR@399`
  - `mean ΔLPIPS@399`
  - `mean ΔtLPIPS@399`
  - `both_seeds_tlpips_negative_399`
- one paragraph explicitly comparing this rerun against the previous `local-softmatch` run

**Step 4: Verify run artifacts exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/summary/summary.json'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_localsoftmatchfix400_pair/summary/per_seed.csv'),
    Path('notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

If Task 6 early-stopped, replace this with a smaller existence check for the seed42-only packet.

---

### Task 8: Apply the go/no-go rule and decide whether the whole local-softmatch family is closed

**Files:**
- Modify: `notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Apply the unchanged final decision rule**

Use the final `step399` summary and the existing threshold `0.001371`.

**GO (worth one later replication, but still not thesis mainline):**
- `mean ΔtLPIPS@399 <= -0.001371`
- `mean ΔLPIPS@399 <= 0`
- `mean ΔPSNR@399 >= 0`
- both seeds satisfy `ΔtLPIPS@399 < 0`

**STOP (default):**
- anything else
- including any `mixed` pattern like `PSNR` up but `LPIPS/tLPIPS` not cleanly improved
- including early-stop

**Step 2: Add one extra family-level interpretation rule**

Write this into the note explicitly:
- if this rerun is still `STOP`, then current `local-softmatch family` is closed for this project;
- if this rerun is `GO`, that only means the previous route judgment was partially confounded by loss formulation bias, and the route earns **at most one later replication**, not immediate promotion.

**Step 3: Write the final verdict line into the note**

The note must contain exactly one of:
- `Final verdict: GO (loss-fix rerun is positive enough for one later replication, not thesis mainline)`
- `Final verdict: STOP (loss-fix rerun does not rescue the local-softmatch family)`

Also include:
- one `Boundary:` sentence
- one sentence containing `thesis mainline`
- one sentence explicitly comparing old vs new rerun outcome

**Step 4: Update the discussion brief conservatively**

Add one short dated subsection to `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md` that records:
- this was a **loss-formulation fairness rerun**, not a second method family;
- only the local-softmatch loss formula changed;
- exact experimental shape remained `SelfCap / seed42,43 / 400-step / control=no-extra-loss / treatment=loss-fix local-softmatch`;
- the final verdict;
- one sentence on what the result still does **not** prove.

**Step 5: Update the alignment table without inflating the claim**

Append the new note path under the `VGGT soft-prior 注入后的 stage-2 训练闭环` row in `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`.

Status rules:
- if rerun is `STOP`, keep status `Partial`
- if rerun is `GO`, status still remains `Partial` (optionally append `+ formula-fix positive rerun`), but never upgrade to `Done`

---

### Task 9: Final validation and handoff check

**Files:**
- Read: `notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-direction-expert-discussion-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Run the focused test pack**

Run:
```bash
pytest -q \
  scripts/tests/test_vggt_local_softmatch_loss.py \
  scripts/tests/test_vggt_local_softmatch_lossfix.py \
  scripts/tests/test_vggt_local_softmatch_lossfix_fairness_contract.py \
  scripts/tests/test_vggt_feature_loss_flags.py \
  scripts/tests/test_run_planb_feat_v2_localsoftmatchfix400_pair_contract.py \
  scripts/tests/test_summarize_vggt_localsoftmatch_pair_contract.py \
  scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py \
  scripts/tests/test_runner_args_passthrough.py -q
```

Expected: PASS.

**Step 2: Run a no-overclaim text check**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('notes/2026-03-06-vggt-local-softmatch-lossfix-rerun.md').read_text(encoding='utf-8')
assert 'thesis mainline' in text
assert 'Boundary:' in text
for bad in ['稳定全面优于', '已证明 VGGT 优化桥成立', '彻底证明原版开题全部完成']:
    assert bad not in text, bad
print('ok')
PY
```

Expected: prints `ok`.

**Step 3: Re-answer the single family-level question**

After all artifacts exist, you must be able to answer in one sentence:

```text
只修 local-softmatch 的 loss 公式偏置、其他设置不变之后，这条 local-softmatch family 在本项目里还值得继续投入吗？
```

Expected:
- if `GO`, answer `值得保留一次更完整 replication，但不进入 thesis mainline`;
- if `STOP`, answer `不值得继续投入，当前 local-softmatch family 在本项目内关闭`.
