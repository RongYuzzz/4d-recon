# Owner A（GPU0 / 32GB）后续计划（protocol_v2 next）

日期：2026-02-27  
目标：在已完成 `protocol_v2` 交付（动静解耦 + VGGT 可解释材料 + stage‑2 smoke/full gate/止损）的基础上，用 **极小成本** 继续回答一个关键问题：

> **feature metric loss 是否存在“可解释且不全线退步”的设置？**  
> 若仍无趋势，则把 stage‑2 明确收口为“负结果 + 失败机理”，不再盲烧卡。

依据：
- 决议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- 协议：`docs/protocols/protocol_v2.yaml`
- 现状审计：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

资源约束（硬）：
- 仅用 GPU0（32GB）
- 所有新 run 必须落 `outputs/protocol_v2/...`（不污染 `protocol_v1/v26`）

预算/纪律（硬）：
- **smoke200 gate → 才允许 full600**
- full600 **最多 1 次**（除非出现明确正趋势且另有新增预算决议）
- full600 若相对 `planb_init_600` 命中 **PSNR↓ / LPIPS↑ / tLPIPS↑** 全线劣化：立即止损

---

## Task 0（必须，2h 内结束）：做一次“对照 sanity”确认可比性

目的：确认 `scripts/run_train_planb_feature_loss_v2_selfcap.sh` 在 `lambda=0` 时与 `planb_init_smoke200` **一致/近似一致**（否则说明主线不可比，需要先修对照）。

### 0.1 运行 smoke200（lambda=0）

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0_sanity \
LAMBDA_VGGT_FEAT=0 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

产物：
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/stats/test_step0199.json`

### 0.2 对比 `planb_init_smoke200`（只看 test）

对照：
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`

判定：
- 若出现明显差异（例如 tLPIPS/LPIPS 差异显著大于之前 smoke200 噪声级别）：**先停下**，把“不可比原因”写入 `notes/protocol_v2_planb_feat_smoke200_owner_a.md`，并拉 B 一起定是否需要修脚本/协议。

---

## Task 1（必须，timebox=1 天）：只做 2 个 smoke200 候选（追求“不全线退步”）

核心假设：上一轮 feature loss 可能“过早/过频/覆盖过大”，导致优化被带偏；因此优先尝试 **晚开 + 降频** 与 **稀疏采样** 两条最小改动。

gate 规则（smoke200）：
- 相对 `planb_init_smoke200`，**不接受** test 侧出现“PSNR↓ + LPIPS↑ + tLPIPS↑”三项全劣化；
- 若仅 1 项轻微退步、其余改善/持平，允许进入候选池（但需在审计里写清楚）。

### 1.1 候选 A：晚开 + 降频（smoke200）

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

### 1.2 候选 B：稀疏 patch 采样（smoke200）

> 说明：`token_proj` 的 phi-size=9×9，patch 采样的意义是“减少覆盖/降低约束范围”，不是为了速度。

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=100 \
VGGT_FEAT_RAMP_STEPS=100 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_PATCH_K=4 \
VGGT_FEAT_PATCH_HW=3 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

### 1.3 审计落盘（必须）

把两次 smoke 的：
- 命令（完整 env）
- `stats/test_step0199.json` 的四项指标
- 相对 `planb_init_smoke200` 的 delta
- “是否通过 gate/为什么”

追加写入：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

## Task 2（条件触发，timebox=1 天）：若 smoke200 通过 gate，只跑 1 次 full600

触发条件：Task 1 的两次候选中至少有一次 **不全线退步**，且你能给出“为什么它更合理”的解释。

### 2.1 选择 1 个候选并外推到 full600（最多 1 次）

建议外推规则：
- 若候选来自“晚开 + 降频”：full600 用更晚的 start（例如 300）与更长 ramp（例如 200）
- 若候选来自“patch 采样”：full600 保持同样 patch 设置，避免引入新变量

示例（晚开外推版；如改用 patch 版，请保留 patch 参数不动）：

```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=600 \
RESULT_TAG=planb_feat_v2_full600_lam0.005_start300_ramp200_every16 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=300 \
VGGT_FEAT_RAMP_STEPS=200 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

### 2.2 full600 止损检查（必须）

对照：
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/stats/test_step0599.json`

判定：
- 若出现 **PSNR↓ / LPIPS↑ / tLPIPS↑** 全线劣化：立即止损并停止继续迭代；
- 把止损判定与失败解释追加写入：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

## Handoff（给 B 的“可复制路径清单”）

当 Task 0/1/2 任一完成后，给 B 同步以下内容（用于刷新 report-pack/scoreboard）：
- 新增 run 的 result dir（`outputs/protocol_v2/.../<RESULT_TAG>/`）
- 对应 stats：
  - smoke：`.../stats/test_step0199.json`
  - full：`.../stats/test_step0599.json`（若触发）
- 审计更新：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

