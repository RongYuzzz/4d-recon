# OpenProposal Phase 2 (THUman4.0) — VGGT Pseudomask Mining Implementation Plan

> **Execution note:** 按 Task 顺序逐条执行；每个 Task 的 Expected 通过后再进入下一步。

**Goal:** 在 Phase 1 的 THUman 子集上产出两套可审计的 `pseudo_masks.npz`（`diff` vs `vggt`），并给出可解释证据图 +（若可用）`miou_fg` 体检，为 Phase 3/4 的训练注入提供输入。

**Architecture:** 本 Phase 对齐总计划 `docs/plans/2026-03-02-align-opening-proposal-v1.md` 的 Phase 2（不得与其矛盾）。实现优先复用现有 `scripts/cue_mining.py`（backend=`diff|vggt|zeros`），输出固定 contract：`pseudo_masks.npz + quality.json + viz/overlays`。评测仍 **local-eval only**（不提交任何公开数据帧/GT mask 到 git/PR/report-pack）。

**Tech Stack:** `scripts/cue_mining.py`, VGGT (`facebook/VGGT-1B`), `scripts/eval_masked_metrics.py`（Phase 1）, `pytest`, basic CLI tools (`rg`, `jq` 可选)。

---

### Task 0: Gate Check（确认 Phase 1 已就绪）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 确认 data contract**

Run（本机路径以 Phase 1 为准）：
```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
test -d "$DATA_DIR/images"
test -d "$DATA_DIR/masks"
test -d "$DATA_DIR/sparse/0"
test -d "$DATA_DIR/triangulation"
```

Expected: 全部通过（exit code 0）

**Step 2: 确认有一个 Phase 1 smoke 训练产物可做 anchor**

Run:
```bash
RUN_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600"
test -f "$RUN_DIR/cfg.yml"
test -f "$RUN_DIR/stats/test_step0599.json"
ls "$RUN_DIR/renders"/test_step599_*.png >/dev/null
```

Expected: 通过（Phase 2 的 `miou_fg` 体检与 fg-masked 评测会复用这个 anchor run）

---

### Task 1: VGGT 权重 warmup（一次性下载/缓存，避免后续训练卡住）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 选定 VGGT cache 目录（本机，不入库）**

建议（示例）：
```bash
export VGGT_MODEL_ID="facebook/VGGT-1B"
export VGGT_CACHE_DIR="/root/autodl-tmp/cache/vggt"
mkdir -p "$VGGT_CACHE_DIR"
```

**Step 2: 用 venv python 做一次最小加载**

Run（推荐优先离线自检；若本机尚无缓存再临时在线一次下载）：

离线自检（优先）：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; m=VGGT.from_pretrained('$VGGT_MODEL_ID', cache_dir='$VGGT_CACHE_DIR'); print('ok', type(m))"
```

若失败（cache 不完整/不存在）→ 临时在线一次下载：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; m=VGGT.from_pretrained('$VGGT_MODEL_ID', cache_dir='$VGGT_CACHE_DIR'); print('ok', type(m))"
```

Expected: 打印 `ok <class ...VGGT...>`

---

### Task 2: 跑 cue mining（diff vs vggt），冻结输出 tag

**Files:**
- Modify: *(none)*
- Create: `notes/openproposal_phase2_vggt_pseudomask.md`
- Test: *(none)*

**Step 1: 冻结本 Phase 的 tag 命名（避免后续混乱）**

建议固定（示例，可按需要微调，但一旦写进 note 就冻结）：
- `CUE_TAG_DIFF="openproposal_thuman4_s00_diff_q0.995_ds4_med3"`
- `CUE_TAG_VGGT="openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3"`

**Step 2: 跑 diff backend（cheap baseline）**

Run:
```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
OUT_DIR="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3"

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend diff \
  --temporal_smoothing median3 \
  --overwrite
```

Expected:
- `$OUT_DIR/pseudo_masks.npz`
- `$OUT_DIR/quality.json`
- `$OUT_DIR/viz/grid_frame000000.jpg`
- `$OUT_DIR/viz/overlay_cam02_frame000000.jpg`（legacy alias）

**Step 3: 跑 vggt backend（主要产物）**

Run（注意传入 cache dir；若你已完成 Task 1 的 warmup，建议 `HF_HUB_OFFLINE=1` 保障可复现/不吃网）：
```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
OUT_DIR="outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3"

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend vggt \
  --temporal_smoothing median3 \
  --vggt_model_id "$VGGT_MODEL_ID" \
  --vggt_cache_dir "$VGGT_CACHE_DIR" \
  --vggt_mode crop \
  --overwrite
```

Expected: 同上（npz + quality + viz）

---

### Task 3: QA（质量止损 + 可解释证据图）

**Files:**
- Modify: `notes/openproposal_phase2_vggt_pseudomask.md`
- Create: *(none)*
- Test: *(none)*

**Step 1: 快速止损检查（全黑/全白/严重闪烁）**

Run:
```bash
cat outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3/quality.json
cat outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3/quality.json
```

Expected（软约束，按总计划精神执行）：
- `all_black=false`
- `all_white=false`
- `temporal_flicker_l1_mean` 不应“明显爆炸”（如果很大，优先调 `threshold_quantile` 或加大 `mask_downscale`，但最多改 1–2 次）

**Step 2: 人眼检查 overlay/grid（必须能说清 mask 在选什么）**

打开如下文件（本机查看，不入证据链）：
- `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3/viz/grid_frame000000.jpg`
- `outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3/viz/grid_frame000000.jpg`

验收口径（人话）：
- 不要是“整屏随机噪点”
- 不要长期全 0 或全 1
- 至少在部分帧/视角上，mask 覆盖明显集中在主体/运动区域（允许失败例，但要落盘说明）

---

### Task 4: `miou_fg` 体检（若 Phase 1 数据集 masks 可用）

**Files:**
- Modify: `notes/openproposal_phase2_vggt_pseudomask.md`
- Create: *(none)*
- Test: *(none)*

**Step 1: 用 Phase 1 的 anchor run 计算 `miou_fg`（diff vs vggt）**

说明：
- 这里的 `gt_fg` 是数据集提供的 `masks/`（阈值 0.5 转二值）
- `pred_fg` 是 `pseudo_masks.npz`（阈值 0.5 转二值）
- 只作为 health-check（总计划要求：不设硬阈值，但禁止退化到“接近随机/全黑全白”）

Run（diff）：
```bash
RUN_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600"

python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir "$RUN_DIR" \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --pred_mask_npz outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3/pseudo_masks.npz \
  --compute_miou \
  --lpips_backend dummy

# Avoid overwriting the vggt result (evaluator output path is fixed).
cp "$RUN_DIR/stats_masked/test_step0599.json" "$RUN_DIR/stats_masked/test_step0599_miou_diff.json"
```

Run（vggt）：
```bash
RUN_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600"

python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir "$RUN_DIR" \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --pred_mask_npz outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3/pseudo_masks.npz \
  --compute_miou \
  --lpips_backend dummy

cp "$RUN_DIR/stats_masked/test_step0599.json" "$RUN_DIR/stats_masked/test_step0599_miou_vggt.json"
```

Expected:
- `.../planb_init_600/stats_masked/test_step0599_miou_diff.json` 与 `..._miou_vggt.json` 里出现 `miou_fg` 字段（数值只做参考）

注：如果你不想覆盖同一个输出文件，可在实现时给 evaluator 增加 `--out_suffix`（可选增强；不阻塞 Phase 3/4）。

---

### Task 5: 写 Phase 2 说明文档（对齐开题口径，但不乱 claim）

**Files:**
- Create/Modify: `notes/openproposal_phase2_vggt_pseudomask.md`
- Test: *(none)*

**Step 1: 写清楚“你到底输出了什么 mask”**

在 `notes/openproposal_phase2_vggt_pseudomask.md` 中至少写明：
- 两个 tag 与完整命令行（diff vs vggt）
- mask 的语义：**这里默认是“foreground/dynamic ROI（silhouette 口径）”**，不是“论文 dynamic-region mask”除非你能证明等价
- `quality.json` 摘要（all_black/all_white/flicker）
- 3–5 张成功例 + 1–2 张失败例（只写本机路径；不打包/不入库）
- （若做了）`miou_fg` 体检结果与解释（强调 dataset-provided）

**Step 2: Commit（仅文档）**

```bash
git add notes/openproposal_phase2_vggt_pseudomask.md
git commit -m "docs(notes): Phase2 VGGT/diff pseudomask mining outputs+QA"
```
