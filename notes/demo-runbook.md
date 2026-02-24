# Demo Runbook

## Commands (Defense Live)
1. Gate-1 data entry (skip if already linked)
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
mkdir -p data
if [ ! -e data/selfcap_bar_8cam60f ]; then
  ln -s /root/projects/4d-recon/data/selfcap_bar_8cam60f data/selfcap_bar_8cam60f
fi
test -d data/selfcap_bar_8cam60f/triangulation
```

2. Gate-1 600-step SelfCap demo
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
python third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f/triangulation \
  --output-path outputs/gate1_selfcap_demo_600/keyframes_60frames_step5.npz \
  --frame-start 0 --frame-end 59 --keyframe-step 5
CUDA_VISIBLE_DEVICES=2 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir data/selfcap_bar_8cam60f \
  --init-npz-path outputs/gate1_selfcap_demo_600/keyframes_60frames_step5.npz \
  --result-dir outputs/gate1_selfcap_demo_600 \
  --start-frame 0 --end-frame 60 \
  --max-steps 600 --eval-steps 600 --save-steps 600 \
  --render-traj-path fixed --global-scale 6
```

3. T0 audit (baseline vs zero-velocity)
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
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
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-evidence-pack
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
$PY scripts/pack_evidence.py --repo_root . --out_tar outputs/report_pack_$(date +%F).tar.gz
```

## Playback files
- `outputs/gate1_selfcap_demo_600/videos/traj_4d_step599.mp4`
- `outputs/t0_selfcap/baseline/videos/traj_4d_step199.mp4`
- `outputs/t0_selfcap/zero_velocity/videos/traj_4d_step199.mp4`

## Fallback
- If Gaussians become 0: increase `--global-scale` and re-check `triangulation` density.
- If singular matrix: force `--render-traj-path fixed` and avoid `arc`.
