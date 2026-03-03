# OpenProposal (THUman4.0 未就绪) — SelfCap Smoke for Phase 2–5 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 THUman4.0 缺失期间，用仓库已有的 SelfCap 子片段跑通 **Phase 2–5 的整条流水线（cue mining → weak fusion → VGGT feature loss → export demo）**，把“脚本/参数/路径/产物 contract”全部提前排雷；等 THUman 到位后只需要替换 `DATA_DIR` 即可复用。

**Architecture:** 这是 **pipeline smoke**，不是最终对齐开题的定量结论。SelfCap 没有 `masks/`，因此本 smoke 只做：
- `mask_source=pseudo_mask` 的 `psnr_fg/lpips_fg`（ROI health-check）
- 不做 `miou_fg`（缺 GT masks）

所有新产物写入：
- `outputs/cue_mining/_waiting_thuman/**`
- `outputs/protocol_v3_openproposal/_waiting_thuman/**`
- `outputs/qualitative_local/**`（仅本机观看，不入证据链）

**Tech Stack:** `scripts/cue_mining.py`、`scripts/eval_masked_metrics.py`、FreeTimeGsVanilla trainer、`scripts/run_train_planb_feature_loss_v2_selfcap.sh`、`scripts/make_side_by_side_video.sh`。

---

### Task 0: 固定 SelfCap 载体与通用变量（一次性）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 固定 DATA_DIR（SelfCap 子片段）**

Run:
```bash
REPO_ROOT="$(pwd)"
DATA_DIR="data/selfcap_bar_8cam60f_seg300_360"
test -d "$DATA_DIR/images"
test -d "$DATA_DIR/triangulation"
test -d "$DATA_DIR/sparse/0"
ls "$DATA_DIR/images/02/000000.jpg" >/dev/null
```

Expected: 全部通过。

**Step 2: 固定 venv python**

Run:
```bash
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
test -x "$VENV_PYTHON"
```

---

### Task 1: Phase 2 smoke — cue mining（diff + vggt + zeros）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: diff backend（CPU，便宜）**

Run:
```bash
OUT_DIFF="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_diff_q0.995_ds4_med3"
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIFF" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend diff \
  --temporal_smoothing median3 \
  --overwrite
```

Expected:
- `$OUT_DIFF/pseudo_masks.npz`
- `$OUT_DIFF/quality.json`
- `$OUT_DIFF/viz/grid_frame000000.jpg`

**Step 2: vggt backend（GPU；如果你只有 1 张卡就先跳过）**

Run:
```bash
export VGGT_MODEL_ID="facebook/VGGT-1B"
export VGGT_CACHE_DIR="/root/autodl-tmp/cache/vggt"
mkdir -p "$VGGT_CACHE_DIR"

OUT_VGGT="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3"
CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_VGGT" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend vggt \
  --vggt_model_id "$VGGT_MODEL_ID" \
  --vggt_cache_dir "$VGGT_CACHE_DIR" \
  --vggt_mode crop \
  --temporal_smoothing median3 \
  --overwrite
```

Expected: 同 Step 1（产物齐全）。

**Step 3: zeros backend（control）**

Run:
```bash
OUT_ZEROS="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_zeros_ds4"
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_ZEROS" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend zeros \
  --temporal_smoothing none \
  --overwrite
```

Expected: 产出 `pseudo_masks.npz`（全黑 mask）。

---

### Task 2: Phase 3/4 训练 smoke 的 anchor — 先跑一个最小 Plan‑B init（200 steps）

> 说明：这里不用 `scripts/run_train_planb_init_selfcap.sh` 的默认 `BASELINE_INIT_NPZ`，避免它误用 canonical SelfCap 的 baseline init。  
> 直接复用仓库已有的 Plan‑B init NPZ（若缺失再生成）。

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 确认 Plan‑B init NPZ（若不存在则生成）**

Run:
```bash
INIT_NPZ="outputs/plan_b/$(basename "$DATA_DIR")/init_points_planb_step5.npz"
if [ ! -f "$INIT_NPZ" ]; then
  echo "[WARN] missing $INIT_NPZ; generating via scripts/init_velocity_from_points.py"
  BASELINE_INIT_NPZ="outputs/plan_b/_waiting_thuman_baseline_init/$(basename "$DATA_DIR")/keyframes_60frames_step5.npz"
  mkdir -p "$(dirname "$BASELINE_INIT_NPZ")"
  "$VENV_PYTHON" third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
    --input-dir "$DATA_DIR/triangulation" \
    --output-path "$BASELINE_INIT_NPZ" \
    --frame-start 0 \
    --frame-end 59 \
    --keyframe-step 5
  "$VENV_PYTHON" scripts/init_velocity_from_points.py \
    --data_dir "$DATA_DIR" \
    --baseline_init_npz "$BASELINE_INIT_NPZ" \
    --frame_start 0 \
    --frame_end_exclusive 60 \
    --keyframe_step 5 \
    --out_dir "outputs/plan_b/$(basename "$DATA_DIR")"
fi
test -f "$INIT_NPZ"
echo "INIT_NPZ=$INIT_NPZ"
```

Expected: `INIT_NPZ=...` 且文件存在。

**Step 2: 启动 200-step 训练（Plan‑B init baseline）**

Run:
```bash
TRAINER="third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
CONFIG="default_keyframe_small"
RUN_DIR="outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/planb_init_smoke200"

CUDA_VISIBLE_DEVICES=0 \
"$VENV_PYTHON" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$RUN_DIR" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 200 \
  --eval-steps 200 \
  --save-steps 200 \
  --seed 42 \
  --train-camera-names "02,03,04,05,06,07" \
  --val-camera-names "08" \
  --test-camera-names "09" \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --eval-on-test
```

Expected:
- `$RUN_DIR/cfg.yml`
- `$RUN_DIR/ckpts/ckpt_199.pt`
- `$RUN_DIR/stats/test_step0199.json`
- `$RUN_DIR/renders/test_step199_0000.png`

---

### Task 3: Phase 1/3/4 的评测口径 smoke — `psnr_fg/lpips_fg`（mask_source=pseudo_mask）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 用 VGGT pseudo mask 做 ROI health-check**

Run:
```bash
RUN_DIR="outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/planb_init_smoke200"
PRED_NPZ="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks.npz"
test -f "$PRED_NPZ"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir "$DATA_DIR" \
  --result_dir "$RUN_DIR" \
  --stage test \
  --step 199 \
  --mask_source pseudo_mask \
  --pred_mask_npz "$PRED_NPZ" \
  --bbox_margin_px 32 \
  --lpips_backend auto
```

Expected:
- `$RUN_DIR/stats_masked/test_step0199.json` 存在，且包含 `psnr_fg/lpips_fg/num_fg_frames`

---

### Task 4: Phase 3 smoke — weak-fusion 注入（对照：zeros / vggt / invert-vggt）

> 依赖：先完成 `docs/plans/2026-03-03-openproposal-waiting-thuman4-preflight.md` 的 Task 3（invert 工具）。

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 生成 invert 版 pseudo mask（可选，但推荐）**

Run:
```bash
IN_NPZ="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks.npz"
OUT_INV="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks_invert.npz"
python3 scripts/invert_pseudo_masks_npz.py --in_npz "$IN_NPZ" --out_npz "$OUT_INV" --overwrite
test -f "$OUT_INV"
```

**Step 2: 跑 zeros control（弱监督应当≈无效/接近 baseline）**

Run:
```bash
TRAINER="third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
CONFIG="default_keyframe_small"
INIT_NPZ="outputs/plan_b/$(basename "$DATA_DIR")/init_points_planb_step5.npz"

RUN_Z="outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/weak_zeros_smoke200"
PZ="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_zeros_ds4/pseudo_masks.npz"

CUDA_VISIBLE_DEVICES=1 \
"$VENV_PYTHON" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$RUN_Z" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 200 \
  --eval-steps 200 \
  --save-steps 200 \
  --seed 42 \
  --train-camera-names "02,03,04,05,06,07" \
  --val-camera-names "08" \
  --test-camera-names "09" \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --eval-on-test \
  --pseudo-mask-npz "$PZ" \
  --pseudo-mask-weight 0.5 \
  --pseudo-mask-end-step 200
```

Expected: `$RUN_Z/stats/test_step0199.json` 存在，且训练 log 含 `[WeakFusion] loaded pseudo masks ...`。

**Step 3: 跑 invert-vggt（弱监督“方向更符合强调动态/前景”的直觉版本）**

Run:
```bash
RUN_I="outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/weak_invert_vggt_smoke200"
PI="outputs/cue_mining/_waiting_thuman/selfcap_seg300_360_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks_invert.npz"

CUDA_VISIBLE_DEVICES=1 \
"$VENV_PYTHON" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$RUN_I" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 200 \
  --eval-steps 200 \
  --save-steps 200 \
  --seed 42 \
  --train-camera-names "02,03,04,05,06,07" \
  --val-camera-names "08" \
  --test-camera-names "09" \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --eval-on-test \
  --pseudo-mask-npz "$PI" \
  --pseudo-mask-weight 0.5 \
  --pseudo-mask-end-step 200
```

Expected: `$RUN_I/stats/test_step0199.json` 存在。

---

### Task 5: Phase 4 smoke — Plan‑B + VGGT feature loss v2（200 steps）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 启动 feature-loss v2 runner（会自动 precompute cache）**

Run:
```bash
DATA_DIR="$DATA_DIR" \
RESULT_DIR="outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/planb_feat_v2_smoke200" \
GPU=0 MAX_STEPS=200 \
VENV_PYTHON="$VENV_PYTHON" \
VGGT_MODEL_ID="facebook/VGGT-1B" \
VGGT_MODEL_CACHE_DIR="/root/autodl-tmp/cache/vggt" \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected:
- `.../stats/test_step0199.json`
- `outputs/vggt_cache/**/gt_cache.npz`（runner 打印的 cache out dir 下）

---

### Task 6: Phase 5 smoke — export-only static/dynamic（可选）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 选择 ckpt（来自 Task 2 或 Task 5）**

Run:
```bash
CKPT_PATH="outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/planb_feat_v2_smoke200/ckpts/ckpt_199.pt"
test -f "$CKPT_PATH"
INIT_NPZ="outputs/plan_b/$(basename "$DATA_DIR")/init_points_planb_step5.npz"
test -f "$INIT_NPZ"
```

**Step 2: 导出 static-only / dynamic-only（tau 先用一个固定值做 smoke）**

Run:
```bash
TRAINER="third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
CONFIG="default_keyframe_small"
TAU="0.01"
CKPT_RUN="planb_feat_v2_smoke200"

CUDA_VISIBLE_DEVICES=0 TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
"$VENV_PYTHON" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --result-dir "outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/export_static_${CKPT_RUN}_tau${TAU}" \
  --init-npz-path "$INIT_NPZ" \
  --start-frame 0 \
  --end-frame 60 \
  --render-traj-path fixed \
  --global-scale 6 \
  --train-camera-names "02,03,04,05,06,07" \
  --val-camera-names "08" \
  --test-camera-names "09" \
  --eval-sample-every-test 1 \
  --ckpt-path "$CKPT_PATH" \
  --export-only \
  --export-vel-filter static_only \
  --export-vel-threshold "$TAU"

CUDA_VISIBLE_DEVICES=0 TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
"$VENV_PYTHON" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --result-dir "outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/export_dynamic_${CKPT_RUN}_tau${TAU}" \
  --init-npz-path "$INIT_NPZ" \
  --start-frame 0 \
  --end-frame 60 \
  --render-traj-path fixed \
  --global-scale 6 \
  --train-camera-names "02,03,04,05,06,07" \
  --val-camera-names "08" \
  --test-camera-names "09" \
  --eval-sample-every-test 1 \
  --ckpt-path "$CKPT_PATH" \
  --export-only \
  --export-vel-filter dynamic_only \
  --export-vel-threshold "$TAU"
```

Expected: 两个导出目录下均出现 `videos/*.mp4`，且 log 含 `[Export] applied export_vel_filter ...`。

**Step 3: side-by-side（本机 qualitative_local，不入证据链）**

Run:
```bash
OUT_DIR="outputs/qualitative_local/openproposal_waiting_thuman4"
mkdir -p "$OUT_DIR"

bash scripts/make_side_by_side_video.sh \
  --left "$(ls outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/export_static_${CKPT_RUN}_tau${TAU}/videos/traj_4d_step*.mp4 | head -n 1)" \
  --right "$(ls outputs/protocol_v3_openproposal/_waiting_thuman/$(basename "$DATA_DIR")/export_dynamic_${CKPT_RUN}_tau${TAU}/videos/traj_4d_step*.mp4 | head -n 1)" \
  --out_dir "$OUT_DIR" \
  --out_name "static_vs_dynamic_${CKPT_RUN}_tau${TAU}.mp4" \
  --left_label "static_only tau=${TAU}" \
  --right_label "dynamic_only tau=${TAU}" \
  --overwrite
```

