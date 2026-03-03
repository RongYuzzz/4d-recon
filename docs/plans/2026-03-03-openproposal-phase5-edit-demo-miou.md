# OpenProposal Phase 5 (THUman4.0) — Edit Demo (Removal) + Optional mIoU Implementation Plan

> **Execution note:** 按 Task 顺序逐条执行；每个 Task 的 Expected 通过后再进入下一步。

**Goal:** 交付一个可演示的“动静解耦/移除（removal）”闭环，并在有 dataset-provided masks 的前提下（可选）给出 `miou_fg`（二值前景）作为定量补充。

**Architecture:** 本 Phase 对齐总计划 `docs/plans/2026-03-02-align-opening-proposal-v1.md` 的 Phase 5（不得与其矛盾）。优先做 **export-only + velocity filter** 的 removal demo（最稳、工程量可控），并把“无背景/遮挡导致洞”的 limitation 写死。`miou_fg` 只在 GT masks 存在时启用；默认 `pred_fg` 为 Phase 2 输出的 `pseudo_masks.npz`（阈值 0.5 转二值，来源必须标注为 dataset-provided vs algorithmic）。

**Tech Stack:** `scripts/export_velocity_stats.py`, FreeTimeGsVanilla trainer (`--export-only`, `--export-vel-filter`, `--export-vel-threshold`), `scripts/eval_masked_metrics.py`, `pytest`。

---

### Task 0: Gate Check（Phase 1/4 至少有一个可用 ckpt）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 选择一个“主 ckpt”（优先 Plan‑B baseline 或 Phase 4 最优）**

候选（至少一个存在即可）：
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_600/ckpts/ckpt_599.pt`

Run:
```bash
ls -la outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/*/ckpts/ckpt_599.pt
```

Expected: 至少列出 1 个文件

**Step 2: 固定 `CKPT_PATH`（后续统一复用）**

从上面候选里选一个，写死并自检：
```bash
CKPT_PATH="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt"
test -f "$CKPT_PATH"

# For naming (e.g., planb_init_600 / planb_feat_v2_600)
CKPT_RUN="$(basename "$(dirname "$(dirname "$CKPT_PATH")")")"
echo "CKPT_RUN=$CKPT_RUN"
```

---

### Task 1: 速度统计 + tau 选择（可解释阈值）

**Files:**
- Create: `notes/openproposal_phase5_edit_demo.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: 找到对应的 init npz（Plan‑B init 文件）**

默认路径（按 runner 约定）：
- `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

Run:
```bash
test -f outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz
```

**Step 2: 导出速度统计（step0 vs step599）**

Run（以 `CKPT_PATH` 为准；如果你选了别的 ckpt，文件名会随 `CKPT_RUN` 变化）：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

CKPT_PATH="${CKPT_PATH:-outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt}"
test -f "$CKPT_PATH"
CKPT_RUN="$(basename "$(dirname "$(dirname "$CKPT_PATH")")")"
OUT_MD="notes/openproposal_phase5_velocity_stats_${CKPT_RUN}.md"

"$VENV_PYTHON" scripts/export_velocity_stats.py \
  --init_npz_path outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz \
  --ckpt_path "$CKPT_PATH" \
  --out_md_path "$OUT_MD" \
  --eps 1e-4
```

Expected:
- `notes/openproposal_phase5_velocity_stats_${CKPT_RUN}.md` 生成

**Step 3: 选 tau（可解释，且不调参成无底洞）**

在 `notes/openproposal_phase5_edit_demo.md` 里写死：
- `tau_low = p50(||v||)`（更“激进”的动态分离）
- `tau_high = p90(||v||)`（更“保守”的动态分离）
- 最终 `tau_final` 二选一（以 demo 可解释性为准）

**Step 4: Commit（仅文档）**

```bash
git add "$OUT_MD" notes/openproposal_phase5_edit_demo.md
git commit -m "docs(notes): Phase5 velocity stats + tau candidates for edit demo"
```

---

### Task 2: export-only 静态/动态分支（定性证据 + removal）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 准备通用环境变量**

```bash
REPO_ROOT="$(pwd)"
export VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
export PY="$VENV_PYTHON"
export TRAINER="$REPO_ROOT/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py"
export CONFIG="default_keyframe_small"
export DATA_DIR="data/thuman4_subject00_8cam60f"
export START_FRAME=0
export END_FRAME=60
export INIT_NPZ="outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz"

# Keep consistent with Task 0
export CKPT_PATH="${CKPT_PATH:-outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt}"
export CKPT_RUN="$(basename "$(dirname "$(dirname "$CKPT_PATH")")")"
test -f "$CKPT_PATH"
```

**Step 2: static-only 导出（= removal demo：移除动态/主体）**

Run（用 `tau_final` 替换 `<TAU>`，并确保 `--export-only`；建议显式传入 init_npz 以减少环境差异）：
```bash
TAU="<TAU>"

TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 CUDA_VISIBLE_DEVICES=0 \
"$PY" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --result-dir "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_${CKPT_RUN}_tau${TAU}" \
  --init-npz-path "$INIT_NPZ" \
  --start-frame "$START_FRAME" \
  --end-frame "$END_FRAME" \
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
```

Expected:
- `.../export_static_${CKPT_RUN}_tau*/videos/traj_4d_step599.mp4`（或等价视频）存在（step id 取决于 checkpoint）
- log 中出现 `[Export] applied export_vel_filter: ... kept ...`

**Step 3: dynamic-only 导出（对照）**

```bash
TAU="<TAU>"

TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 CUDA_VISIBLE_DEVICES=0 \
"$PY" "$TRAINER" "$CONFIG" \
  --data-dir "$DATA_DIR" \
  --result-dir "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_${CKPT_RUN}_tau${TAU}" \
  --init-npz-path "$INIT_NPZ" \
  --start-frame "$START_FRAME" \
  --end-frame "$END_FRAME" \
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

Expected: 同上（产出 dynamic-only 视频）

TIP（避免 step 号搞错）：导出后用下面命令找视频文件名：
```bash
ls -la "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_${CKPT_RUN}_tau${TAU}/videos"/*.mp4
ls -la "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_${CKPT_RUN}_tau${TAU}/videos"/*.mp4
```

**Step 4: 产出 side-by-side（只渲染，不拼 GT）**

```bash
OUT_DIR="outputs/qualitative_local/openproposal_phase5"
mkdir -p "$OUT_DIR"

bash scripts/make_side_by_side_video.sh \
  --left "$(ls outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_${CKPT_RUN}_tau${TAU}/videos/traj_4d_step*.mp4 | head -n 1)" \
  --right "$(ls outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_${CKPT_RUN}_tau${TAU}/videos/traj_4d_step*.mp4 | head -n 1)" \
  --out_dir "$OUT_DIR" \
  --out_name "static_vs_dynamic_${CKPT_RUN}_tau${TAU}.mp4" \
  --left_label "static_only tau=${TAU}" \
  --right_label "dynamic_only tau=${TAU}" \
  --overwrite
```

---

### Task 3: 可选 `miou_fg`（二值前景，来源必须标注）

**Files:**
- Modify: `notes/openproposal_phase5_edit_demo.md`
- Create: *(none)*
- Test: *(none)*

**Step 1: 确认 Phase 2 的 pred mask 存在**

Run（选择 vggt 或 diff 任一作为 pred_fg）：
```bash
PRED_NPZ="outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks.npz"
test -f "$PRED_NPZ"
```

**Step 2: 用 anchor run 计算 `miou_fg`（gt=dataset masks）**

```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --pred_mask_npz "$PRED_NPZ" \
  --compute_miou \
  --lpips_backend dummy

# Avoid overwriting other masked eval outputs.
cp \
  "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599.json" \
  "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_miou_phase5.json"
```

Expected:
- 输出 JSON 内出现 `miou_fg`

**Step 3: 文档声明（必须）**

在 `notes/openproposal_phase5_edit_demo.md` 写清：
- `gt_fg`：THUman4.0 dataset-provided masks（非人工标注，来源说明）
- `pred_fg`：Phase 2 算法产生 pseudo mask（阈值 0.5）
- `miou_fg` 仅作为前景一致性参考，不等价于“人工 GT instance segmentation”

---

### Task 4: 最终交付清单（DoD for Phase 5）

**Files:**
- Modify: `notes/openproposal_phase5_edit_demo.md`
- Create: *(none)*
- Test: *(none)*

**Step 1: 在文档末尾列出可复核路径**

至少包含：
- `tau_final` 及其依据（p50/p90）
- static-only / dynamic-only 两条视频路径（本机）
- side-by-side 路径（本机）
- （可选）`miou_fg` 数值与 JSON 路径
- limitation：遮挡背景不可见 → removal 可能出现洞/残影（必须写）

**Step 2: Commit（仅文档）**

```bash
git add notes/openproposal_phase5_edit_demo.md
git commit -m "docs(notes): Phase5 edit/removal demo deliverables + optional miou_fg"
```

---

## Exit Criteria（Phase 5 验收）

- removal demo 可播放（static-only 视频）+ 有对照（dynamic-only 或 side-by-side）
- 速度阈值选择过程可解释（有 stats 与 tau_final）
- （若做 `miou_fg`）来源声明完整且口径明确
