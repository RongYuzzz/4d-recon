# T0 Gradient Check Log

## Scope
- Target params: `velocities`, `durations`
- Source: trainer runtime log + CSV (`--t0-grad-log-path`)
- PASS rule: both runs are finite and have non-zero gradient signals.

## Run command (current audit)
```bash
cd /root/projects/4d-recon
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
mkdir -p outputs/t0_selfcap
python third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f/triangulation \
  --output-path outputs/t0_selfcap/keyframes_60frames_step5.npz \
  --frame-start 0 --frame-end 59 --keyframe-step 5
CUDA_VISIBLE_DEVICES=2 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir /root/projects/4d-recon/data/selfcap_bar_8cam60f \
  --init-npz-path outputs/t0_selfcap/keyframes_60frames_step5.npz \
  --result-dir outputs/t0_selfcap/baseline \
  --start-frame 0 --end-frame 60 \
  --max-steps 200 --eval-steps 200 --save-steps 200 \
  --render-traj-path fixed --global-scale 12 \
  --t0-debug-interval 50 \
  --t0-grad-log-path outputs/t0_selfcap/baseline/t0_grad.csv

CUDA_VISIBLE_DEVICES=2 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir /root/projects/4d-recon/data/selfcap_bar_8cam60f \
  --init-npz-path outputs/t0_selfcap/keyframes_60frames_step5.npz \
  --result-dir outputs/t0_selfcap/zero_velocity \
  --start-frame 0 --end-frame 60 \
  --max-steps 200 --eval-steps 200 --save-steps 200 \
  --render-traj-path fixed --global-scale 12 \
  --t0-debug-interval 50 \
  --t0-grad-log-path outputs/t0_selfcap/zero_velocity/t0_grad.csv \
  --force-zero-velocity-for-t0
```

## Output files
- Baseline grad log: `outputs/t0_selfcap/baseline/t0_grad.csv`
- Zero-velocity grad log: `outputs/t0_selfcap/zero_velocity/t0_grad.csv`
- Baseline video: `outputs/t0_selfcap/baseline/videos/traj_4d_step199.mp4`
- Zero-velocity video: `outputs/t0_selfcap/zero_velocity/videos/traj_4d_step199.mp4`

## CSV schema note
- Current trainer columns: `step,vel_grad_norm,duration_grad_norm,vel_grad_finite,duration_grad_finite`
- Compatibility: if future columns change to `grad_v_norm/grad_duration_norm`, checker should accept both names.

## Status (`2026-02-24T11:06:16+08:00`)
- Dataset used: `/root/projects/4d-recon/data/selfcap_bar_8cam60f` (real selfcap)
- Baseline: `rows=200, finite=True, nonzero_v=200, nonzero_d=200`
- Zero-velocity: `rows=200, finite=True, nonzero_v=200, nonzero_d=200`
- Conclusion: `PASS`

## Historical note
- Earlier fixture fallback run exists under archived directories:
  - `outputs/t0_selfcap/baseline_prev_20260224_110513`
  - `outputs/t0_selfcap/zero_velocity_prev_20260224_110513`
