# SelfCap Gate-1 Run (Owner B)

日期：2026-02-24
当时工作树：`/root/projects/4d-recon/.worktrees/owner-b-20260224`（历史记录）

建议：在主阵地 `/root/projects/4d-recon` 复现（命令本身不依赖 worktree 路径）。

## 1) Adapter 产数命令

```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz data/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0
```

## 2) combine_frames 命令

```bash
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
python third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f/triangulation \
  --output-path outputs/gate1_selfcap_bar_8cam60f/keyframes_60frames_step5.npz \
  --frame-start 0 \
  --frame-end 59 \
  --keyframe-step 5
```

## 3) 训练命令（GPU1）

```bash
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
CUDA_VISIBLE_DEVICES=1 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir data/selfcap_bar_8cam60f \
  --init-npz-path outputs/gate1_selfcap_bar_8cam60f/keyframes_60frames_step5.npz \
  --result-dir outputs/gate1_selfcap_bar_8cam60f \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 60 \
  --eval-steps 60 \
  --save-steps 60 \
  --render-traj-path fixed \
  --global-scale 6
```

## 4) 关键产物

- 视频：`outputs/gate1_selfcap_bar_8cam60f/videos/traj_4d_step59.mp4`
- 指标：`outputs/gate1_selfcap_bar_8cam60f/stats/val_step0059.json`
- 初始化 NPZ：`outputs/gate1_selfcap_bar_8cam60f/keyframes_60frames_step5.npz`

## 5) 动态性验收（velocity）

```text
vel_norm min/mean/max: 0.0 0.016971351578831673 0.4995685815811157
nonzero count: 92681 of 92749
```

结论：`velocity` 非全 0，满足 Gate-1 真动态 smoke 验收条件。
