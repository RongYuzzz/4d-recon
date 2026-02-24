# 4D Reconstruction Workspace

This workspace tracks the execution of `2026-02-12-4d-reconstruction-execution.md`.

## Structure
- `third_party/`: external repositories
- `data/`: datasets or symlinks
- `outputs/`: training and rendering outputs
- `notes/`: decision logs and environment notes
- `scripts/`: runnable experiment scripts

## Data Adapter (COLMAP sparse -> triangulation NPY)

Use `scripts/export_triangulation_from_colmap_sparse.py` when your dataset does not provide
`points3d_frame*.npy` / `colors_frame*.npy` directly.

### Gate-0 (smoke test, static copy)

```bash
python scripts/export_triangulation_from_colmap_sparse.py \
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

### Gate-1 (dynamic-ish, per-frame visible points)

```bash
python scripts/export_triangulation_from_colmap_sparse.py \
  --colmap_data_dir data/scene01/colmap \
  --out_dir data/scene01/triangulation \
  --mode visible_per_frame \
  --frame_start 0 \
  --frame_end -1 \
  --max_points 200000
```

Notes:
- Script auto-groups multi-camera images by frame index parsed from image names
  (e.g. `cam00_frame000123.jpg` -> frame `123`).
- If `pycolmap` is unavailable, it falls back to `third_party/FreeTimeGsVanilla/datasets/read_write_model.py`.
- Output manifest: `frame_manifest.csv`.

## SelfCap Adapter (HF `zju3dv/SelfCap-Dataset`)

`bar-release.tar.gz` 实测目录结构为：
- `videos/*.mp4`
- `pcds/*.ply`（每帧 sparse point cloud）
- `dense_pcds/*.ply`（稀疏采样的 dense point cloud）
- `optimized/{intri.yml,extri.yml}`

本仓库提供 `scripts/prepare_selfcap_for_freetime.py`，将上述结构转换为：
- `triangulation/points3d_frame*.npy` + `colors_frame*.npy`
- `colmap/sparse/0/{cameras.bin,images.bin,points3D.bin}`

### 60 帧点云段（不解视频，先跑数据链路）

```bash
python scripts/prepare_selfcap_for_freetime.py \
  --selfcap_root data/raw/selfcap/extracted/bar-release \
  --out_root data/scene_selfcap_bar_200_260_noimg \
  --frame_start 200 \
  --frame_end 260 \
  --image_width 2112 \
  --image_height 3760
```

### 如果要直接训练（需要图像），增加 `--extract_images`

前提：`selfcap_root/videos/<cam>.mp4` 存在，且机器上有 `ffmpeg`/`ffprobe`。

```bash
python scripts/prepare_selfcap_for_freetime.py \
  --selfcap_root data/raw/selfcap/extracted/bar-release \
  --out_root data/scene_selfcap_bar_200_260 \
  --frame_start 200 \
  --frame_end 260 \
  --extract_images
```

## Gate Smoke Entrypoints

### Gate-0 (real HF sample + static_repeat triangulation)

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

### Gate-1 (real HF sample + per_frame_sparse triangulation)

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
- `RENDER_TRAJ_PATH`: render trajectory profile (for example `fixed`).
- `RENDER_TRAJ_TIME_FRAMES`: trajectory frame count override (mostly for Gate-1).
- `EXTRA_TRAIN_ARGS`: raw extra flags forwarded to trainer.

## Synthetic Scene Helper

`scripts/generate_synthetic_scene01.py` 依赖 `Pillow`。若环境缺失可安装：

```bash
pip install Pillow
```
