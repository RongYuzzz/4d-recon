# Owner A (GPU0) protocol_v2 GPU Follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 GPU0 上补齐/固化 `protocol_v2` 阶段二的 GPU 侧可复现交付（动静分层导出可编辑 demo + framediff gate 诊断产物），并（可选）用极小 smoke200 seed 补充确认“无稳定候选”，把产物路径 handoff 给 B 打包与更新文档。

**Architecture:** 不新增 full600（除非出现新的预算决议文件）；优先复用现有 ckpt 做 `--export-only` 导出，新增分析/可视化尽量落到 `outputs/report_pack/diagnostics/`（方便离线包打包与审计）。如需新增训练，仅允许 `MAX_STEPS=200` 的 smoke200 且严格 timebox。

**Tech Stack:** bash、`third_party/FreeTimeGsVanilla/.venv/bin/python`、`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`、`scripts/analyze_vggt_gate_framediff.py`、现有产物树 `outputs/protocol_v1/` + `outputs/protocol_v2/`。

---

## Constraints / Invariants（必须遵守）

- 仅使用 **GPU0**：所有 GPU 命令必须显式 `CUDA_VISIBLE_DEVICES=0`。
- 不新增 full600：除非仓库新增预算决议文件（并在计划/验收里引用路径）。
- 任何新增 run 必须落在 `outputs/protocol_v2/...`，不得覆盖 `protocol_v1/v26` 证据链。
- 新增训练仅 smoke200：必须显式 `MAX_STEPS=200`，且目录内必须有 `cfg.yml` + `stats/test_step0199.json`。
- Handoff 原则：A 只产出“可审计路径 + 一句话结论”，由 B 负责刷新 scoreboard / report-pack / evidence tar。

---

### Task 0: Preflight（10 分钟）

**Files:**
- Read: `third_party/FreeTimeGsVanilla/.venv/bin/python`
- Read: `data/selfcap_bar_8cam60f/`
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt`

**Step 1: 确认 GPU0 可用**

Run: `nvidia-smi -L`  
Expected: 存在 GPU 0（32GB）。

**Step 2: 确认关键路径存在**

Run:
```bash
ls -la third_party/FreeTimeGsVanilla/.venv/bin/python
ls -la data/selfcap_bar_8cam60f/images data/selfcap_bar_8cam60f/triangulation
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt
```
Expected: 均存在。

---

### Task 1: 动静分层 export-only 复现（Plan-B vs Plan-B+Feat）（30-60 分钟）

**目的：**把 “static-only / dynamic-only” 的导出过程固化为可复现命令（依赖 ckpt，不需要重训），并补齐可审计输出目录。

**Files:**
- Read: `notes/protocol_v2_static_dynamic_tau.md`（已存在则直接取 `tau_final`）
- Read: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- Read: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt`
- Create/Update: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau*/videos/`
- Create/Update: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau*/videos/`
- Create/Update: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau*/videos/`
- Create/Update: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau*/videos/`

**Step 1: 取阈值 τ（优先复用既有口径）**

- 若 `notes/protocol_v2_static_dynamic_tau.md` 已给出 `tau_final`，直接使用。
- 若缺失，先停下，不在本计划内重新发明阈值口径；先找 B 对齐阈值来源。

（当前 repo 已出现的口径示例：`tau_final=0.075436`，以现有 note 为准。）

**Step 2: Export planb_init_600 static-only**

Run:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
CKPT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt
TAU=0.075436
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau${TAU}

CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
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

Expected:
- 日志包含 `[Export] applied export_vel_filter: mode=static_only ...`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau*/videos/traj_4d_step599.mp4` 存在

**Step 3: Export planb_init_600 dynamic-only**

Run:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
CKPT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt
TAU=0.075436
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau${TAU}

CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
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
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau*/videos/traj_4d_step599.mp4` 存在

**Step 4: Export planb_feat_v2_full600 static/dynamic（同 τ）**

Run（static）:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
CKPT=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt
TAU=0.075436
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau${TAU}

CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
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

Run（dynamic）:
```bash
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA=data/selfcap_bar_8cam60f
CKPT=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt
TAU=0.075436
OUT=outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau${TAU}

CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
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

**Step 5: Handoff 给 B**

把最终 4 个视频路径发给 B（用于 report-pack README/manifest 引用）：
- `export_planb_static_tau*/videos/traj_4d_step599.mp4`
- `export_planb_dynamic_tau*/videos/traj_4d_step599.mp4`
- `export_planbfeat_static_tau*/videos/traj_4d_step599.mp4`
- `export_planbfeat_dynamic_tau*/videos/traj_4d_step599.mp4`

---

### Task 2: framediff gate 诊断落盘（CPU 任务，可与 Task 1 并行）（15-30 分钟）

**目的：**把 framediff gate 的统计诊断产物固化到 `outputs/report_pack/diagnostics/`（小文件，易打包），并标注 p=0.10 vs p=0.02 的差异。

**Files:**
- Read: `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
- Read: `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz`
- Modify/Create: `outputs/report_pack/diagnostics/`（新增带后缀的输出文件）
- Update: `notes/protocol_v2_framediff_gate_viz.md`（如需补链接）

**Step 1: 对 p=0.10 cache 生成诊断（如已存在可跳过）**

Run:
```bash
python3 scripts/analyze_vggt_gate_framediff.py \
  --cache_npz outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
  --out_dir outputs/report_pack/diagnostics/gate_framediff_p010
```

Expected:
- `outputs/report_pack/diagnostics/gate_framediff_p010/gate_framediff_heatmap.png` 等文件存在

**Step 2: 对 p=0.02 cache 生成诊断**

Run:
```bash
python3 scripts/analyze_vggt_gate_framediff.py \
  --cache_npz outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
  --out_dir outputs/report_pack/diagnostics/gate_framediff_p002
```

Expected:
- `outputs/report_pack/diagnostics/gate_framediff_p002/gate_framediff_heatmap.png` 等文件存在

**Step 3: Handoff 给 B**

把以下路径发给 B（用于离线包与 report-pack 指针）：
- `outputs/report_pack/diagnostics/gate_framediff_p010/`
- `outputs/report_pack/diagnostics/gate_framediff_p002/`
- `notes/protocol_v2_framediff_gate_viz.md`

---

### Task 3（可选，严格 timebox=2h）: smoke200 仅做“seed 稳定性补充”并收口

**触发条件：**仅当需要更硬的“无稳定候选”结论或准备触发预算讨论时执行；否则跳过。

**Files:**
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0/`
- Update: `notes/protocol_v2_planb_feat_smoke200_owner_a.md`

**Step 1: 跑 1 个新增 seed（示例 seed=44）**

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=0 MAX_STEPS=200 SEED=44 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_USE_CONF=0 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected:
- `.../cfg.yml` + `.../stats/test_step0199.json` 存在

**Step 2: 计算 delta vs `planb_init_smoke200` 并写入审计**

Run:
```bash
CUR=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0/stats/test_step0199.json
BASE=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json
python3 - <<'PY'
import json, os
base=json.load(open(os.environ["BASE"]))
cur=json.load(open(os.environ["CUR"]))
for k in ["psnr","ssim","lpips","tlpips"]:
    print(k, cur[k]-base[k])
PY
```

判定口径：
- `tLPIPS` 的“可置信改善阈值”参考 `docs/report_pack/2026-02-27-v2/README.md` 中的噪声带（2x 噪声带）。
- 若仍不满足“≥2 seeds 同时 ΔtLPIPS<=0 且 ΔLPIPS<=0 且幅度显著大于噪声带”，明确写入 `notes/protocol_v2_planb_feat_smoke200_owner_a.md`：**收口，不再扩展 sweep**。

**Step 3: Handoff 给 B**

把新增 result dir + stats 路径发给 B：
- `outputs/protocol_v2/selfcap_bar_8cam60f/<RESULT_TAG>/stats/test_step0199.json`

