# protocol_v2 Dual-GPU Smoke Trend Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 利用 GPU0 并行推进 `protocol_v2` 的 stage‑2（Plan‑B + VGGT feature metric）**smoke200 趋势探索**，重点验证“更强 gating（framediff top‑p 更稀疏）+ 更保守 schedule（晚开/低频）”是否能减少或消除对 `tLPIPS` 的退步；**不新增 full600**（除非形成新增预算决议）。

**Architecture:** 在不改训练代码的前提下，复用现有入口 `scripts/run_train_planb_feature_loss_v2_selfcap.sh`，仅改超参（`VGGT_FEAT_GATING=framediff`、`VGGT_FEAT_GATING_TOP_P`、`LAMBDA_VGGT_FEAT`、`VGGT_FEAT_START_STEP`、`VGGT_FEAT_EVERY`），每个 run 结束后立刻做 delta 与 gate 判定并写入审计 note，及时 handoff 给 B 汇总 scoreboard / report-pack。

**Tech Stack:** bash + `scripts/run_train_planb_feature_loss_v2_selfcap.sh`、Python（delta 计算）、`notes/protocol_v2_planb_feat_smoke200_owner_a.md`（审计真源）。

---

## Constraints / Invariants（必须遵守）

- 仅使用 **GPU0**：所有训练命令必须显式 `GPU=0`。
- 仅新增 smoke200：`MAX_STEPS=200`；**不新增 full600**（无预算决议不得跑）。
- 新产物路径：仅写入 `outputs/protocol_v2/...`（共享 cache/plan_b 若已存在则不覆盖）。
- 每个 run 必须满足最小可审计产物：`cfg.yml` + `stats/test_step0199.json`。
- 审计真源：每个 run 的命令 + 指标 + delta + gate 判定必须写入 `notes/protocol_v2_planb_feat_smoke200_owner_a.md`。

---

### Task 0: Preflight（10 分钟）

**Step 1: 确认 GPU0 可用**

Run:
```bash
nvidia-smi -L
```

Expected: 至少看到 GPU 0。

**Step 2: 确认 venv / cache / init 存在（不生成新 cache）**

Run:
```bash
ls -la third_party/FreeTimeGsVanilla/.venv/bin/python
ls -la outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz
ls -la outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz
```

Expected: 文件存在。

**Important Note（framediff top‑p 与 cache 的关系）**

- 当前 `token_proj` cache 内的 `gate_framediff` 是**预先按某个 top‑p 二值化后的 mask**（见 `outputs/vggt_cache/*/meta.json:framediff_top_p`）。  
- 训练时 `VGGT_FEAT_GATING_TOP_P` 会再次对 `gate_framediff` 做 top‑p 选择；如果你直接把 `top_p` 改小但仍复用旧 cache（例如 cache 是 0.10），会变成“在二值 mask 上随机选子集”，不再对应真实高帧差区域。
- 因此：**要测试更稀疏的 framediff top‑p，必须使用新的 cache 目录（不同 framediff_top_p）**，不得覆盖旧 cache。

---

### Task 1: smoke200（framediff gating 更稀疏，3 个 runs）

> 注：历史 `framediff_top_p=0.10` 的 smoke200 未通过 gate；本轮只改 `top_p` 更稀疏（更少像素参与 feature loss），并保持“晚开/低频”思路，避免早期收敛被拉偏。

**Files:**
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_*`
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

#### Run A1（λ=0.005, start150, every16, framediff p=0.02）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16/cfg.yml`
- `.../stats/test_step0199.json`
Additional cache artifacts (auto-generated if missing):
- `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/meta.json`（期望 `framediff_top_p=0.02`）

#### Run A2（λ=0.005, start200, every16, framediff p=0.02）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=200 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

#### Run A3（λ=0.002, start200, every16, framediff p=0.02）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.002 \
VGGT_FEAT_START_STEP=200 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

---

### Task 2: Gate 判定 + 审计落盘（每个 run 完成后立刻做）

**Files:**
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 1: 计算 delta vs `planb_init_smoke200`**

Run（把 `CUR` 改成对应 run 的 stats 路径）：
```bash
CUR=outputs/protocol_v2/selfcap_bar_8cam60f/<RUN_TAG>/stats/test_step0199.json
BASE=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json
python3 - <<'PY'
import json, os
base=json.load(open(os.environ["BASE"]))
cur=json.load(open(os.environ["CUR"]))
for k in ["psnr","ssim","lpips","tlpips"]:
    print(k, cur[k]-base[k])
PY
```

**Step 2: gate 判定（写清规则 + 结论）**

- smoke gate（沿用现行口径）：若命中 `PSNR↓ + LPIPS↑ + tLPIPS↑` 三项全劣化 → gate fail；否则 gate pass（但需写明是否为“优先候选”）。
- 把完整命令（env）、指标、delta、判定写入：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

### Task 3: Handoff to B（每天一次，5 分钟）

把下列信息同步给 B（用于当日刷新 metrics/scoreboard/packaging）：

- 每个新 run 的目录：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/<RUN_TAG>/`
  - `.../stats/test_step0199.json`
- A 侧审计更新位置：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

### Discussion Triggers（仅在必要/关键时才讨论）

满足任一触发条件才建议找同行/导师/专家讨论“是否追加 1 次 full600 预算”：

1) **同一候选**（同一超参）在 smoke200 上出现“tLPIPS 不退步（ΔtLPIPS ≤ 0）且 LPIPS 不变差（ΔLPIPS ≤ 0）”，并且差异明显大于噪声（由 B 的 seed sweep 给出噪声带）。  
2) framediff gating 形成明确机制解释（为什么更稀疏 top‑p 会更稳）且能指向具体失败片段改善（可用 side-by-side 佐证）。

否则：按 `mixed trend + failure analysis` 收口，不新增 full600。

---

### Done Criteria（A 侧完成判据）

- 完成 A1/A2/A3 三个 smoke200，且每个 run 均满足：`cfg.yml + stats/test_step0199.json` + 已写审计（命令/指标/delta/gate）。  
- 已把 run 路径清单 handoff 给 B，用于更新 scoreboard/report-pack。
