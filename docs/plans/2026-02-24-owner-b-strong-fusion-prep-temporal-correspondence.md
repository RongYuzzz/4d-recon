# Owner B Strong Fusion Prep: Temporal Correspondences + Baseline Sweep (GPU1)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改动现有训练主线（避免与 A 的 weak-fusion 同文件冲突）的前提下，补齐 strong-fusion 所需的“可落地输入”：为 `data/selfcap_bar_8cam60f` 预计算**时序稀疏对应**（temporal correspondences），固化 I/O 契约与可视化证据；并在 GPU1 跑一组 baseline 小 sweep，产出可直接进证据包的对比视频与指标条目。

**Non-Goal (本轮不做):**
- 不在本分支直接把 strong loss 接进 `simple_trainer_freetime_4d_pure_relocation.py`（该文件预计会被 A 改动；强融合接入建议等 A 合并 weak-fusion 后再做，减少 merge 冲突）。

**Parallel Safety:** 本计划主要新增脚本与文档，不触碰 trainer 主文件；可与 A/C 完全并行。

**Default Resources:** B 使用 `GPU1` 仅跑短训练（`MAX_STEPS=200~600`）；correspondence 预计算走 CPU。

---

## Task B12: 创建隔离 Worktree/分支

**Files:**
- None (worktree only)

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260224-strongprep .worktrees/owner-b-20260224-strongprep main
cd .worktrees/owner-b-20260224-strongprep
git status --porcelain=v1
```

Expected:
- `status` 输出为空

---

## Task B13: 冻结 strong-fusion 输入契约与损失设计口径（文档优先）

**Files:**
- Create: `notes/attention_loss_design.md`

内容要求（写到能直接指导实现）：
- **对应数据契约（NPZ）**：`temporal_corr.npz` 最小 keys（建议）：
  - `camera_names`: `str[V]`（按 `images/` 文件夹排序）
  - `frame_start`: `int`
  - `num_frames`: `int`
  - `image_width`, `image_height`: `int`
  - `src_cam_idx`: `int16[N]`
  - `src_frame_offset`: `int16[N]`
  - `dst_frame_offset`: `int16[N]`（建议只做 `+1`，也允许更一般）
  - `src_xy`: `float32[N,2]`（像素坐标，x/y）
  - `dst_xy`: `float32[N,2]`
  - `weight`: `float32[N]`（默认 1.0，后续可放入置信度/遮挡过滤）
- **对应来源策略**：
  - 兜底：OpenCV KLT（本计划实现）
  - 目标：VGGT attention/top-k 对应（后续替换对应来源，但契约不变）
- **强融合 loss 的最小版本（实现建议）**：
  - 先做 “flow-warp photometric”：
    `L_corr = mean_i w_i * |I_pred(src, x) - I_gt(dst, x')|`
  - 强制要求：loss 默认关闭；开启后只影响前 N steps（例如 2k），避免后期劣化
- 明确 3 个验收点：
  1. 训练不崩（no NaN / no OOM）
  2. `velocity` 分布不退化到全 0
  3. 视觉上减少 flicker/断裂（哪怕指标提升不明显）

验收：
- 文档里出现“契约 keys 列表 + loss 公式 + 默认关闭策略”

---

## Task B14: 实现 temporal correspondences 预计算脚本（OpenCV KLT，CPU 可跑）

**Files:**
- Create: `scripts/extract_temporal_correspondences_klt.py`
- Create: `scripts/tests/test_temporal_correspondences_klt_contract.py`

脚本要求（最小 CLI）：
- `--data_dir`：例如 `data/selfcap_bar_8cam60f`
- `--camera_ids`：可选（如 `02,03,...`）；不传则按 `images/` 子目录全选
- `--frame_start`、`--num_frames`
- `--max_tracks_per_pair`：默认 `500`
- `--min_track_len`：默认 `1`（先只做 t->t+1）
- `--out_npz`：例如 `outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`
- `--viz_dir`：可选，输出 1-2 张 overlay（便于汇报截图）

实现建议（可直接照做）：
- 对每个 camera：
  - 读 `frame t` 与 `frame t+1`（灰度）
  - `cv2.goodFeaturesToTrack` 取 `p0`
  - `cv2.calcOpticalFlowPyrLK` 得到 `p1` + `status` + `err`
  - 过滤掉越界点、`status==0`、err 过大
  - 写入全局数组（带 cam_idx、src/dst frame_offset）
- `viz`：输出 `frame000000_to_000001_cam02.jpg`（画箭头）

单测要求（不依赖 pytest）：
- 用 `scripts/generate_synthetic_scene01.py` 生成极小数据（2 cams × 3 frames）
- 跑 extractor 并断言：
  - NPZ 存在
  - 必要 keys 存在
  - `src_xy.shape[1]==2` 且 N>0（synthetic 里有运动）

---

## Task B15: 在 SelfCap bar 8cam60f 上生成对应文件 + 可视化（不入库）

**Files:**
- Create (runtime, not committed): `outputs/correspondences/selfcap_bar_8cam60f_klt/*`
- Create: `notes/selfcap_temporal_corr_klt.md`

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-strongprep
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
mkdir -p outputs/correspondences/selfcap_bar_8cam60f_klt/viz
$PY scripts/extract_temporal_correspondences_klt.py \
  --data_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --max_tracks_per_pair 500 \
  --out_npz outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
  --viz_dir outputs/correspondences/selfcap_bar_8cam60f_klt/viz
```

记录到 `notes/selfcap_temporal_corr_klt.md`：
- 命令行（可复现）
- N（总对应数）
- 每相机平均对应数（可选）
- `viz/` 截图位置

验收：
- `outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz` 存在且非空
- `viz/` 至少 1 张图

---

## Task B16: GPU1 baseline 小 sweep（为 midterm/最终表格提前攒证据）

**Files:**
- None (runtime only)

建议只做 3 条短跑（200~600 steps），固定输入不变：
- 输入：
  - `INPUT_DIR=data/selfcap_bar_8cam60f/triangulation`
  - `DATA_DIR=data/selfcap_bar_8cam60f`
  - `START_FRAME=0 END_FRAME=60 KEYFRAME_STEP=5 GPU_ID=1 CONFIG=default_keyframe_small`
- 变量：只改 `EXTRA_TRAIN_ARGS`（例如 `--global-scale`）

Run（示例 3 条）：
```bash
cd /root/projects/4d-recon
MAX_STEPS=200 EVAL_STEPS=200 SAVE_STEPS=200 RENDER_TRAJ_PATH=fixed \
EXTRA_TRAIN_ARGS='--global-scale 4' \
bash third_party/FreeTimeGsVanilla/run_pipeline.sh \
  data/selfcap_bar_8cam60f/triangulation data/selfcap_bar_8cam60f \
  outputs/sweep_selfcap_baseline_gs4 0 60 5 1 default_keyframe_small

MAX_STEPS=200 EVAL_STEPS=200 SAVE_STEPS=200 RENDER_TRAJ_PATH=fixed \
EXTRA_TRAIN_ARGS='--global-scale 6' \
bash third_party/FreeTimeGsVanilla/run_pipeline.sh \
  data/selfcap_bar_8cam60f/triangulation data/selfcap_bar_8cam60f \
  outputs/sweep_selfcap_baseline_gs6 0 60 5 1 default_keyframe_small

MAX_STEPS=200 EVAL_STEPS=200 SAVE_STEPS=200 RENDER_TRAJ_PATH=fixed \
EXTRA_TRAIN_ARGS='--global-scale 8' \
bash third_party/FreeTimeGsVanilla/run_pipeline.sh \
  data/selfcap_bar_8cam60f/triangulation data/selfcap_bar_8cam60f \
  outputs/sweep_selfcap_baseline_gs8 0 60 5 1 default_keyframe_small
```

验收：
- 每条都有：
  - `outputs/.../videos/traj_4d_step*.mp4`
  - `outputs/.../stats/val_step*.json`
- 用 `scripts/build_report_pack.py` 生成 `metrics.csv` 后可看到新增条目（不要求指标提升，只要可比较、可复现）

---

## Task B17 (可选，等 A 合并 weak-fusion 后再做): strong loss 接入训练的最小 patch

**说明：** 本任务会修改 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`，建议等 A 的 weak-fusion 合并到 `main` 后，B 再开新分支做，避免重复解决冲突。

交付目标：
- trainer 新增 `--temporal-corr-npz ...`、`--lambda-corr ...`，默认关闭
- 开启后训练可跑通（GPU1 60 steps），并产出与 baseline 可比较的视频

