# Owner A (GPU0) protocol_v2 Stage‑2 Trade-off Diagnosis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不新增 `full600` sweep 预算的前提下，把“`PSNR↑` 但 `LPIPS/tLPIPS↑`”这条 stage‑2 现象补齐为**可解释的证据链**；并用 **≤2 次 smoke200** 验证是否存在“至少不伤 `tLPIPS`”的 feature‑loss 设置。

**Architecture:** 以现有 `protocol_v2` 产物为真源：先做**定性证据**（side‑by‑side + 动静解耦对比），把 trade‑off 说清楚；再做**极小试探**（只改 1 个变量的 smoke200）判断是否值得向负责人申请 1 次额外 `full600` 预算。所有新产物仅写入 `outputs/protocol_v2/...` 或 `outputs/qualitative/...`，并把命令/指标/结论追加到 A 的审计 note。

**Tech Stack:** bash、Python、ffmpeg、PyTorch、`third_party/FreeTimeGsVanilla` trainer、`scripts/run_train_planb_feature_loss_v2_selfcap.sh`、`scripts/make_side_by_side_video.sh`、`scripts/export_velocity_stats.py`。

---

### Task 0: Preconditions / Invariants（30 分钟）

**Files:**
- Read: `docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- Read: `docs/protocols/protocol_v2.yaml`
- Read/Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 1: 确认资源约束与止损纪律**
- 仅用 GPU0（32GB）。
- 只允许 `smoke200`（最多 2 次）；**不新增 `full600`**（除非拿到新增预算决议）。
- 所有新 run 必须落 `outputs/protocol_v2/selfcap_bar_8cam60f/<RESULT_TAG>/`（需包含 `cfg.yml` + `stats/*.json` + `videos/*.mp4`）。

**Step 2: 快速 sanity（路径存在）**

Run:
```bash
nvidia-smi -L
ls -la third_party/FreeTimeGsVanilla/.venv/bin/python
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt
```
Expected: 路径存在、GPU0 可用。

---

### Task 1: “Trade-off 说清楚”定性证据（半天）

**Files:**
- Create: `outputs/qualitative/planb_vs_baseline/*.mp4`
- Create/Update: `notes/protocol_v2_stage2_tradeoff_qual.md`

**Step 1: 生成 3 个 side‑by‑side 对比视频（用统一工具，便于离线包收录）**

1) `baseline_600` vs `planb_init_600`（对齐阶段一收益）：
```bash
bash scripts/make_side_by_side_video.sh \
  --left outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4 \
  --right outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4 \
  --left_label baseline_600 \
  --right_label planb_init_600 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name baseline_600__vs__planb_init_600__step599.mp4 \
  --overwrite
```

2) `planb_init_600` vs `planb_feat_v2_full600_*`（trade‑off 主证据）：
```bash
bash scripts/make_side_by_side_video.sh \
  --left outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4 \
  --right outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/videos/traj_4d_step599.mp4 \
  --left_label planb_init_600 \
  --right_label planb_feat_v2_full600_start300_ramp200_every16 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_init_600__vs__planb_feat_v2_full600_start300_ramp200_every16__step599.mp4 \
  --overwrite
```

3) `baseline_600` vs `planb_feat_v2_full600_*`（从 baseline 视角展示整体效果）：
```bash
bash scripts/make_side_by_side_video.sh \
  --left outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4 \
  --right outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/videos/traj_4d_step599.mp4 \
  --left_label baseline_600 \
  --right_label planb_feat_v2_full600_start300_ramp200_every16 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name baseline_600__vs__planb_feat_v2_full600_start300_ramp200_every16__step599.mp4 \
  --overwrite
```

Expected: `outputs/qualitative/planb_vs_baseline/*.mp4` 生成成功（`scripts/pack_evidence.py` 会自动收录该目录 mp4）。

**Step 2: 把“看点/失败点”写成可答辩口径**
- 在 `notes/protocol_v2_stage2_tradeoff_qual.md` 写 1 页以内：
  - 三个视频的路径
  - “PSNR↑但 LPIPS/tLPIPS↑”在画面上对应的现象（例如纹理更锐但更闪/更漂）
  - 1 个代表性失败片段（写帧号/时间点即可）

---

### Task 2: 对 `planb_feat_v2_full600_*` 做动静解耦导出（半天，可并行）

**Files:**
- Create: `notes/velocity_stats_planb_feat_v2_full600_start300.md`
- Create: `notes/protocol_v2_static_dynamic_tau_planb_feat_v2_full600.md`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau*/videos/`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau*/videos/`

**Step 1: 统计该 run 的速度分布（用于选 τ）**

Run:
```bash
python3 scripts/export_velocity_stats.py \
  --init_npz_path outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz \
  --ckpt_path outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt \
  --out_md_path notes/velocity_stats_planb_feat_v2_full600_start300.md
```
Expected: `notes/velocity_stats_planb_feat_v2_full600_start300.md` 含 step599 的 `p50/p90`。

**Step 2: 选 2 个 τ 做 A/B（推荐：p50 / p90）**
- 把 `τ_low/τ_high` 与理由写入：`notes/protocol_v2_static_dynamic_tau_planb_feat_v2_full600.md`

**Step 3: export-only 渲染 static-only / dynamic-only（τ=τ_low，再做 τ_high）**

Run（改 `TAU/OUT/CKPT`，其余保持一致）：
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
CKPT=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt

TAU=0.10
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau${TAU}

TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --ckpt-path "$CKPT" \
  --export-only \
  --render-traj-path fixed \
  --export-vel-filter static_only \
  --export-vel-threshold "$TAU"
```

Run（dynamic-only，改 `OUT` + filter）：
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
CKPT=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt

TAU=0.10
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau${TAU}

TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --ckpt-path "$CKPT" \
  --export-only \
  --render-traj-path fixed \
  --export-vel-filter dynamic_only \
  --export-vel-threshold "$TAU"
```
Expected:
- Log 含 `[Export] applied export_vel_filter ... kept ...`
- 视频生成：`.../videos/traj_4d_step599.mp4`

**Step 4: 选 `τ_final` 并写“可编辑性/失败边界”**
- `notes/protocol_v2_static_dynamic_tau_planb_feat_v2_full600.md` 必须包含：
  - `τ_low/τ_high/τ_final`
  - static/dynamic 最终视频路径
  - 1 个失败例（慢动/抖动背景等）

---

### Task 3: ≤2 次 smoke200（只改 1 个变量，验证是否能减轻 tLPIPS 退步）

**Files:**
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_*/`

**Common setup:**
- 复用 cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
- 对照基线：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`

**Step 1: 候选 C1（只改 λ：0.005 → 0.002，保持“晚开+降频”）**
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16 \
LAMBDA_VGGT_FEAT=0.002 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_USE_CONF=1 \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

**Step 2: 候选 C2（只改 conf：on → off，保持 λ 与 schedule）**
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_USE_CONF=0 \
VGGT_FEAT_GATING=none \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

**Step 3: gate 判定与审计落盘（必须）**
- 每个 run 完成后，检查：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/<RESULT_TAG>/stats/test_step0199.json`
  - 记录相对 `planb_init_smoke200` 的 ΔPSNR/ΔLPIPS/ΔtLPIPS
- gate 规则（沿用）：**不接受** test 侧命中 “PSNR↓ + LPIPS↑ + tLPIPS↑” 三项全劣化。
- 把命令 + 指标 + delta + gate 结论追加到：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

### Task 4: 决策点（10 分钟）

**Step 1: 若 C1/C2 任意一个在 smoke200 上出现明确“减轻 tLPIPS 退步”的趋势**
- 不直接开跑 `full600`（预算已到上限）。
- 给负责人发一条“新增预算申请”信息（附：候选参数 + smoke200 指标 + 为什么值得再给 1 次 full600）。

**Step 2: 若两次 smoke200 都无趋势**
- 宣布 stage‑2 结论收口为：**trade‑off/负结果 + failure analysis**（不再增加 GPU 训练）。
- 用 Task 1/2 的定性证据把它写成可答辩材料（对齐 `4D-Reconstruction-v2.md` 的叙事）。

---

### Handoff to B（每次产出后即时同步）

把下面“可复制路径清单”发给 B（用于刷新 metrics/scoreboard/tarball/narrative）：
- 新 smoke run 目录（含 `cfg.yml` + `stats/test_step0199.json` + `videos/traj_4d_step199.mp4`）
- 新 export-only 目录（static/dynamic 视频路径）
- 新增定性视频（`outputs/qualitative/planb_vs_baseline/*.mp4`）
- 审计 note 更新位置：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

