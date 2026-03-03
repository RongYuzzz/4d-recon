# protocol_v2 Dual-GPU Smoke Trend Implementation Plan (Owner B / GPU1)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 Owner B 使用 GPU1 并行推进 `protocol_v2` 的 stage‑2 smoke200（不新增 full600），用 **seed sweep + 小网格** 量化“噪声带”和“是否存在稳定候选”，并把结论当日回填到 `report-pack`（scoreboard/README/manifest），为后续“是否申请 1 次 full600 预算验证外推”提供硬证据。

**Architecture:** B 侧只做“可复现 + 可汇总”的 GPU 运行（不改代码），所有 run 名称包含 `seed`，并坚持 `outputs/protocol_v2/...` 的最小可审计产物；每天统一刷新 `metrics.csv` + scoreboard，并输出“是否触发讨论”的结论（不提前拉同行/导师/专家）。

**Tech Stack:** bash + `scripts/run_train_planb_feature_loss_v2_selfcap.sh`、`scripts/build_report_pack.py`、`scripts/summarize_scoreboard.py`、`scripts/pack_evidence.py`、`docs/report_pack/2026-02-27-v2/*`。

---

## Constraints / Invariants（必须遵守）

- 仅使用 **GPU1**：所有训练命令必须显式 `GPU=1`。
- 仅新增 smoke200：`MAX_STEPS=200`；**不新增 full600**（无预算决议不得跑）。
- 新产物路径：仅写入 `outputs/protocol_v2/...`（共享 cache/plan_b 若已存在则不覆盖）。
- 每个 run 必须满足最小可审计产物：`cfg.yml` + `stats/test_step0199.json`。
- 每天收口输出：刷新 `outputs/report_pack/metrics.csv` + `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`，并把当天结论写入 `docs/report_pack/2026-02-27-v2/README.md`（追加一小节即可）。

---

### Task 0: Preflight（15 分钟）

**Step 1: 确认 GPU1 存在且可用**

Run:
```bash
nvidia-smi -L
```

Expected: 看到 GPU 1（32GB）。

**Step 2: 代码与单测基线（避免跑到一半才发现环境坏）**

Run:
```bash
pytest -q scripts/tests
```

Expected: PASS。

**Step 3: 记录关键事实（用于避免“无效变量”浪费 GPU）**

Run:
```bash
cat outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json | head -n 80
```

Expected:
- `has_conf=false`（token_proj 不提供 conf；`VGGT_FEAT_USE_CONF` 对 token_proj 理论上不生效，差异多半是噪声）
- `has_gate_framediff=true` 且 `framediff_top_p=0.1`（framediff gate 已存在，但 top‑p 若要改小，需要新 cache；见 A 侧计划）

---

### Task 1: Seed Sweep（估计噪声带，4 个 runs）

> 目的：用“同一超参跨 seed”的差异估计 smoke200 的噪声带，避免把 1e‑4 级别的波动当成趋势。

**Files:**
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_*_s42_gpu1/`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_*_s43_gpu1/`

#### Run B1（λ=0 sanity, seed=42）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_lam0_sanity_s42_gpu1 \
LAMBDA_VGGT_FEAT=0.0 \
VGGT_FEAT_PHI_NAME=token_proj \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

#### Run B2（λ=0 sanity, seed=43）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=43 \
RESULT_TAG=planb_feat_v2_smoke200_lam0_sanity_s43_gpu1 \
LAMBDA_VGGT_FEAT=0.0 \
VGGT_FEAT_PHI_NAME=token_proj \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

#### Run B3（当前最像“可外推”的 schedule, seed=42）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s42_gpu1 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

#### Run B4（同超参, seed=43）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=43 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s43_gpu1 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

---

### Task 2: 小网格（2 个 runs，用于对比“更晚开/更小 λ”）

#### Run B5（更晚开：start200, λ=0.005）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start200_ramp50_every16_s42_gpu1 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=200 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

#### Run B6（更小 λ：start200, λ=0.002）

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=42 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.002_start200_ramp50_every16_s42_gpu1 \
LAMBDA_VGGT_FEAT=0.002 \
VGGT_FEAT_START_STEP=200 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

---

### Task 3: Delta / 噪声带估计（每个 run 完成后立即做）

**Step 1: 对每个 run 计算 delta vs `planb_init_smoke200`**

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

**Step 2: 估计 smoke200 噪声带（至少给出 tLPIPS 的 seed 差异）**

- 计算 `B3 vs B4` 的 `tLPIPS` 差异（同超参不同 seed）。
- 计算 `B1 vs B2` 的 `tLPIPS` 差异（feature loss 关闭时的 seed 差异）。
- 输出一个结论：`tLPIPS` 的“可置信改善阈值”至少要大于多少（例如 > 2×噪声带）。

**Step 3: 把噪声带结论同步给 A（用于解释小幅 delta）**

---

### Task 4: Report-pack 汇总（当天收口，20 分钟）

**Files:**
- Update: `outputs/report_pack/metrics.csv`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- Update: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: 刷新 metrics.csv**

Run:
```bash
python3 scripts/build_report_pack.py
```

Expected: `outputs/report_pack/metrics.csv` 行数增加（包含新 smoke200 runs）。

**Step 2: 重建 v2 smoke scoreboard（step=199）**

Run:
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --stage test \
  --step 199
```

**Step 3: README 追加“2026-02-28 dual-GPU smoke sweep”小节**

写清三点即可（不用长文）：
- 本日新增 runs 列表（含 seed）
- 噪声带估计（尤其 tLPIPS）
- 是否触发“讨论/预算申请”（见下方 Discussion Triggers）

---

### Discussion Triggers（仅在必要/关键时才讨论）

满足任一条件，才建议拉同行/导师/专家讨论“是否追加 1 次 full600 预算验证外推”：

1) **同一候选**在 ≥2 个 seed 上同时满足：`ΔtLPIPS ≤ 0` 且 `ΔLPIPS ≤ 0`（对照 `planb_init_smoke200`），并且改善幅度显著大于噪声带。  
2) 与 A 侧 framediff 更稀疏 gating 的结果结合后，出现“机制 + 数据”一致的解释（不是单次偶然）。

否则：继续按 `mixed trend + failure analysis` 收口，不新增 full600。

---

### Done Criteria（B 侧完成判据）

- 完成 B1–B6 共 6 个 smoke200（GPU1），且每个 run 均满足：`cfg.yml + stats/test_step0199.json`。
- 已完成 seed 噪声带估计，并同步给 A。
- 已刷新 `metrics.csv` 与 `scoreboard_smoke200.md`，并在 `docs/report_pack/2026-02-27-v2/README.md` 追加当日收口结论。

