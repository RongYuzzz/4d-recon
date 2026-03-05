# 4D Reconstruction Workspace

本仓库用于复现实验 / 产出证据链 / 固化协议（protocol）与运行脚本。

- 执行总览：`docs/execution/2026-02-12-4d-reconstruction-execution.md`
- 文档索引：`docs/README.md`
- 现场演示 Runbook：`notes/demo-runbook.md`

日常可运行命令主要集中在本文件与 `notes/demo-runbook.md`。

## protocol_v2（双阶段）提交入口

- 开题对外版（v2）：`4D-Reconstruction-v2.md`
- 阶段二证据包（v2）：`docs/report_pack/2026-02-27-v2/README.md`
- 02-27 验收记录：`docs/reviews/2026-02-27/acceptance-2026-02-27.md`
- 说明：`4D-Reconstruction.md` 为历史原稿/存档，不再作为提交版，避免口径打架。

## Protocol（Single Source of Truth）

冻结训练/评测协议（stage-1 evidence）：`docs/protocol.yaml`（指向 `docs/protocols/protocol_v*.yaml`）。

规则：
- 不要静默改动 frame range / camera split / seed / 关键超参。
- 如需改协议：新增 `docs/protocols/protocol_vX.yaml`，并显式更新 `docs/protocol.yaml`。

Stage‑2（opening‑proposal alignment / academic completeness）：
- 决议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- 新 runs 记录：`docs/protocols/protocol_v2.yaml`（与 v26 evidence chain 分开，避免互相污染）

## Structure

- `scripts/`: runnable experiment scripts（训练 / 评测 / 可视化 / 打包）
- `scripts/tests/`: `pytest` contract tests
- `third_party/FreeTimeGsVanilla/`: forked training code（多数 runner 默认使用其 `.venv`）
- `data/`: datasets or symlinks（常见结构：`images/`、`triangulation/`、`sparse/`）
- `outputs/`: run artifacts（append‑only；不要手工改历史结果）
- `docs/`、`notes/`: 协议、计划、复盘、审计与解释性记录

## Quickstart（SelfCap canonical）

前置：
- SelfCap tarball：`data/selfcap/bar-release.tar.gz`
- FreeTimeGsVanilla venv python（默认）：`third_party/FreeTimeGsVanilla/.venv/bin/python`
- Tip：大多数 runners 支持通过 `VENV_PYTHON=/path/to/python` 覆盖默认 venv。

### 0) Tests（可选但推荐）

```bash
pytest -q
# 或仅跑脚本合约测试：
pytest -q scripts/tests/test_*.py
```

### 1) 适配数据（Gate‑1 canonical）

推荐主入口：`scripts/adapt_selfcap_release_to_freetime.py`

- 输入 tarball：`data/selfcap/bar-release.tar.gz`
- 输出目录：`data/selfcap_bar_8cam60f`
- 默认推荐参数：`--camera_ids 02,03,04,05,06,07,08,09 --frame_start 0 --num_frames 60 --image_downscale 2`

```bash
PY="${VENV_PYTHON:-third_party/FreeTimeGsVanilla/.venv/bin/python}"
$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz data/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0
```

该 canonical 路线直接读取 `bar-release.tar.gz`，不依赖系统 `ffmpeg`/`ffprobe`。

Tips:
- 若 `--output_dir` 已存在且非空，重新生成请加 `--overwrite`（会清理已知子目录：`images/`、`sparse/`、`triangulation/`）。
- 若你只想导出 `triangulation + sparse/0`（跳过视频解码），可用 `--no_images --image_width ... --image_height ...`。

### 2) 训练（SelfCap canonical runners）

训练入口（默认对齐 `docs/protocol.yaml`；常用 knobs 通过 env var 暴露：`GPU`、`RESULT_DIR`、`DATA_DIR`、`VENV_PYTHON`、`MAX_STEPS`、`EXTRA_TRAIN_ARGS` 等）：

```bash
# Baseline
GPU=0 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600 \
bash scripts/run_train_baseline_selfcap.sh

# Plan‑B init（生成/复用 init npz）
GPU=0 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600 \
bash scripts/run_train_planb_init_selfcap.sh

# Stage‑2 runner（protocol_v2）
GPU=1 RESULT_DIR=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feature_loss_v2_600 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

### 3) 指标汇总 + 证据包（report pack / evidence）

```bash
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md

DATE_TAG=$(date +%F)
python3 scripts/pack_evidence.py --repo_root . --out_tar artifacts/report_packs/report_pack_${DATE_TAG}.tar.gz
sha256sum artifacts/report_packs/report_pack_${DATE_TAG}.tar.gz | tee -a artifacts/report_packs/SHA256SUMS.txt
```

说明：
- `artifacts/` 用于存放“不适合进 git”的大文件（见：`artifacts/README.md`）。建议提交 `artifacts/report_packs/SHA256SUMS.txt`，但不要提交 `*.tar.gz`。

### Legacy / Alternative（SelfCap）

历史流程 `scripts/prepare_selfcap_for_freetime.py` 属于非主入口（legacy）。

差异（人话版）：
- canonical：`adapt_selfcap_release_to_freetime.py` 直接吃 `bar-release.tar.gz`，不依赖系统 `ffmpeg/ffprobe`，用于 Gate‑1/T0 的标准输入。
- legacy：`prepare_selfcap_for_freetime.py` 吃“已解压目录结构”，`--extract_images` 抽帧时需要系统 `ffmpeg/ffprobe`，适合你已经有解压目录或想调试 yml->COLMAP 写入/抽帧到 `images/` 的场景。

## Data Adapter（COLMAP sparse -> triangulation NPY）

当数据集不直接提供 `points3d_frame*.npy` / `colors_frame*.npy` 时，使用：
`scripts/export_triangulation_from_colmap_sparse.py` 从 COLMAP sparse 导出 `triangulation/`。

### Gate‑0（smoke test, static copy）

```bash
python3 scripts/export_triangulation_from_colmap_sparse.py \
  --colmap_data_dir data/scene01/colmap \
  --out_dir data/scene01/triangulation \
  --mode static_copy \
  --frame_start 0 \
  --frame_end -1 \
  --max_points 200000 \
  --keyframe_step 5 \
  --keyframe_emit keyframes_with_next \
  --link_mode symlink
```

### Gate‑1（dynamic-ish, per-frame visible points）

```bash
python3 scripts/export_triangulation_from_colmap_sparse.py \
  --colmap_data_dir data/scene01/colmap \
  --out_dir data/scene01/triangulation \
  --mode visible_per_frame \
  --frame_start 0 \
  --frame_end -1 \
  --max_points 200000
```

Notes:
- Script auto-groups multi-camera images by frame index parsed from image names（例：`cam00_frame000123.jpg` -> frame `123`）。
- If `pycolmap` is unavailable, it falls back to `third_party/FreeTimeGsVanilla/datasets/read_write_model.py`.
- Output manifest: `frame_manifest.csv`.

## Gate Smoke Entrypoints

### Gate‑0（real HF sample + static_repeat triangulation）

`scripts/run_gate0_smoke.sh` usage:

```bash
bash scripts/run_gate0_smoke.sh \
  <source_hf_dir> \
  [adapted_dir] \
  [result_dir] \
  [gpu_id] \
  [num_frames] \
  [keyframe_step] \
  [config]
```

Example:

```bash
EXTRA_TRAIN_ARGS='--global-scale 6' \
MAX_STEPS=40 \
RENDER_TRAJ_PATH=fixed \
bash scripts/run_gate0_smoke.sh \
  data/hf_4dgv_cook8_source \
  data/gate0_4dgv_cook8_gs6 \
  outputs/gate0_4dgv_cook8_gs6 \
  0 24 5 default_keyframe_small
```

### Gate‑1（real HF sample + per_frame_sparse triangulation）

`scripts/run_gate1_smoke.sh` usage:

```bash
bash scripts/run_gate1_smoke.sh \
  <source_hf_dir> \
  [per_frame_sparse_dir] \
  [adapted_dir] \
  [result_dir] \
  [gpu_id] \
  [frame_start] \
  [frame_end|-1:auto] \
  [keyframe_step] \
  [config]
```

Common env passthrough:
- `MAX_STEPS`: override trainer max/eval/save steps.
- `RENDER_TRAJ_PATH`: render trajectory profile（例如 `fixed`）。
- `RENDER_TRAJ_TIME_FRAMES`: trajectory frame count override（mostly for Gate‑1）。
- `EXTRA_TRAIN_ARGS`: raw extra flags forwarded to trainer.

## Synthetic Scene Helper

`scripts/generate_synthetic_scene01.py` 依赖 `Pillow`。若环境缺失可安装：

```bash
python3 -m pip install Pillow
```
