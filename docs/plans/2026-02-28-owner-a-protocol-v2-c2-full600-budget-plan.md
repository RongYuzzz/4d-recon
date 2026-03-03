# protocol_v2 C2(noconf) full600 Verification Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在已完成 stage‑2 trade-off 诊断（定性证据 + C1/C2 smoke200）的基础上，若获得新增预算，**仅补跑 1 次** `full600` 来验证 C2（`VGGT_FEAT_USE_CONF=0`）能否把 “tLPIPS 退步变小” 的 smoke 趋势外推到 full600；否则不再新增 full600，阶段二收口为 mixed trend + failure analysis。

**Architecture:** 保持与现有 `planb_feat_v2_full600_lam0.005_start300_ramp200_every16` **完全同参**，只改 `VGGT_FEAT_USE_CONF=0`（隔离变量）。训练完成后补齐：定量（stats + delta）、定性（side-by-side）、可编辑性（static/dynamic export-only）。

**Tech Stack:** bash + `scripts/run_train_planb_feature_loss_v2_selfcap.sh`、Python（快速 delta 计算）、ffmpeg（`scripts/make_side_by_side_video.sh`）、FreeTime4D trainer export-only。

---

### Task 0: Budget Gate（必须先过，10 分钟）

**Rule:** 未拿到“新增 full600 预算决议”→ **不允许跑 full600**（只允许整理证据/口径）。

**Step 1: 给负责人提交 1 条预算申请（附最小证据）**
- 申请内容：新增 **1 次 full600**，仅验证 C2：`VGGT_FEAT_USE_CONF=0`。
- 证据指针：
  - C2 smoke：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf/stats/test_step0199.json`
  - 对照 baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`
  - 审计：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 2: 记录“是否批准/批准人/日期”到审计 note**
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

### Task 1: full600（C2 noconf，条件触发：预算批准后才执行）

**Files:**
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/`
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 1: Preflight**

Run:
```bash
nvidia-smi -L
ls -la third_party/FreeTimeGsVanilla/.venv/bin/python
ls -la outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz
```

**Step 2: 运行 full600（只改 conf=0）**

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=600 \
RESULT_TAG=planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=300 \
VGGT_FEAT_RAMP_STEPS=200 \
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

Expected artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/cfg.yml`
- `.../stats/test_step0599.json`
- `.../videos/traj_4d_step599.mp4`
- `.../ckpts/ckpt_599.pt`

**Step 3: stoploss 判定（必须）**
- 对照：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/stats/test_step0599.json`
- 规则：若命中 **PSNR↓ / LPIPS↑ / tLPIPS↑** 全线劣化 → 记录止损判定并停止继续任何新增 full600。

（可选）快速 delta 脚本：
```bash
python3 - <<'PY'
import json, pathlib
base=json.loads(pathlib.Path("outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/stats/test_step0599.json").read_text())
cur=json.loads(pathlib.Path("outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/stats/test_step0599.json").read_text())
for k in ["psnr","lpips","tlpips"]:
    print(k, cur[k]-base[k])
PY
```

**Step 4: 审计落盘（必须）**
在 `notes/protocol_v2_planb_feat_smoke200_owner_a.md` 追加：
- 完整命令（env）
- test/val 指标
- vs `planb_init_600` 与 vs “conf-on full600” 的 delta
- gate/止损结论 + 下一步建议（继续/收口）

---

### Task 2: 定性与可编辑性补齐（export-only + side-by-side）

**Files:**
- Create: `outputs/qualitative/planb_vs_baseline/*.mp4`
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_noconf_*/videos/traj_4d_step599.mp4`
- Update: `notes/protocol_v2_stage2_tradeoff_qual.md`（如结论发生变化）

**Step 1: 生成 2 个 side-by-side（隔离 conf 变量）**

Run（planb_init vs noconf）：
```bash
bash scripts/make_side_by_side_video.sh \
  --left outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4 \
  --right outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/videos/traj_4d_step599.mp4 \
  --left_label planb_init_600 \
  --right_label planb_feat_v2_full600_noconf \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_planbfeat_full600_noconf_step599.mp4 \
  --overwrite
```

Run（conf-on vs noconf）：
```bash
bash scripts/make_side_by_side_video.sh \
  --left outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/videos/traj_4d_step599.mp4 \
  --right outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/videos/traj_4d_step599.mp4 \
  --left_label planb_feat_full600_conf \
  --right_label planb_feat_full600_noconf \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planbfeat_full600_conf__vs__noconf_step599.mp4 \
  --overwrite
```

**Step 2: export-only 动静解耦（固定 τ=0.139066，保证与现有 planb_feat export 可比）**

> 注：FreeTime4D trainer 即使 export-only 也需要 `--init-npz-path`（用于初始化后再 load ckpt）。

static-only:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz
CKPT=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/ckpts/ckpt_599.pt

TAU=0.139066
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_noconf_static_tau${TAU}

TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --ckpt-path "$CKPT" \
  --export-only \
  --render-traj-path fixed \
  --export-vel-filter static_only \
  --export-vel-threshold "$TAU"
```

dynamic-only（同 τ）：
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz
CKPT=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/ckpts/ckpt_599.pt

TAU=0.139066
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_noconf_dynamic_tau${TAU}

TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
CUDA_VISIBLE_DEVICES=0 "$VENV_PYTHON" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --ckpt-path "$CKPT" \
  --export-only \
  --render-traj-path fixed \
  --export-vel-filter dynamic_only \
  --export-vel-threshold "$TAU"
```

**Step 3: 更新 trade-off 口径（如结论变化）**
- Update: `notes/protocol_v2_stage2_tradeoff_qual.md`
- 仅当出现“ΔtLPIPS 明显下降/转正”等变化时，补充一句话与证据指针（scoreboard + 视频）。

---

### Task 3: Handoff to B（每次产出后即时同步）

把下面路径清单发给 B（用于当日刷新 metrics/scoreboard/tarball/narrative）：
- 新 full600 run：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/`
  - `.../stats/test_step0599.json`
  - `.../videos/traj_4d_step599.mp4`
- 新 side-by-side：`outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_noconf_step599.mp4`、`outputs/qualitative/planb_vs_baseline/planbfeat_full600_conf__vs__noconf_step599.mp4`
- 新 export-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_noconf_{static,dynamic}_tau0.139066/videos/traj_4d_step599.mp4`
- 审计更新：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

---

### Done Criteria（A 侧完成判据）

满足其一即 Done：
1) 预算未批准：已在审计 note 记录“不跑 full600”的决策与理由；不再新增 full600。  
2) 预算已批准：已完成 1 次 full600（C2 noconf）+ stoploss 判定 + 必要定性/导出 + handoff 给 B。

