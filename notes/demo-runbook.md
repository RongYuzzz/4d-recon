# Demo Runbook

目标：在主阵地 `/root/projects/4d-recon` 现场可复现（不依赖 `.worktrees/...` 路径）。

## Commands (Defense Live)

0. Quick sanity
```bash
cd /root/projects/4d-recon
test -f data/selfcap/bar-release.tar.gz
test -f third_party/FreeTimeGsVanilla/.venv/bin/activate
```

1. Gate-1 data entry (skip if already exists)
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz data/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
test -d data/selfcap_bar_8cam60f/triangulation
```

2. Protocol v1 (Baseline / Ours-Weak / Control) full runs (GPU2)

说明：
- 下面 3 条命令的默认参数已对齐 `docs/protocol.yaml`（相机 split/帧段/seed/global_scale/keyframe_step）。
- 会同时产出 `val_step*.json` + `test_step*.json`，并在 test 上计算 `tLPIPS`（需要 `eval_sample_every_test=1`，默认已启用）。

```bash
cd /root/projects/4d-recon

# Baseline (FreeTimeGsVanilla)
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600 \
bash scripts/run_train_baseline_selfcap.sh

# Ours-Weak (cue mining + mask-weighted photometric loss)
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600 \
bash scripts/run_train_ours_weak_selfcap.sh

# Control: same weak path, but constant mask (no cue)
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600 \
bash scripts/run_train_control_weak_nocue_selfcap.sh
```

3. T0 audit (baseline vs zero-velocity, GPU2)
```bash
cd /root/projects/4d-recon
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
mkdir -p outputs/t0_selfcap
python third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f/triangulation \
  --output-path outputs/t0_selfcap/keyframes_60frames_step5.npz \
  --frame-start 0 --frame-end 59 --keyframe-step 5

CUDA_VISIBLE_DEVICES=2 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir data/selfcap_bar_8cam60f \
  --init-npz-path outputs/t0_selfcap/keyframes_60frames_step5.npz \
  --result-dir outputs/t0_selfcap/baseline \
  --start-frame 0 --end-frame 60 \
  --max-steps 200 --eval-steps 200 --save-steps 200 \
  --render-traj-path fixed --global-scale 12 \
  --t0-debug-interval 50 \
  --t0-grad-log-path outputs/t0_selfcap/baseline/t0_grad.csv

CUDA_VISIBLE_DEVICES=2 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir data/selfcap_bar_8cam60f \
  --init-npz-path outputs/t0_selfcap/keyframes_60frames_step5.npz \
  --result-dir outputs/t0_selfcap/zero_velocity \
  --start-frame 0 --end-frame 60 \
  --max-steps 200 --eval-steps 200 --save-steps 200 \
  --render-traj-path fixed --global-scale 12 \
  --t0-debug-interval 50 \
  --t0-grad-log-path outputs/t0_selfcap/zero_velocity/t0_grad.csv \
  --force-zero-velocity-for-t0
```

4. Pack evidence
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
$PY scripts/pack_evidence.py --repo_root . --out_tar outputs/report_pack_$(date +%F).tar.gz
```

## Playback files
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600/videos/traj_4d_step599.mp4`
- `outputs/t0_selfcap/baseline/videos/traj_4d_step199.mp4`
- `outputs/t0_selfcap/zero_velocity/videos/traj_4d_step199.mp4`

## Fallback
- If Gaussians become 0: increase `--global-scale` and re-check `triangulation` density.
- If singular matrix: force `--render-traj-path fixed` and avoid `arc`.
