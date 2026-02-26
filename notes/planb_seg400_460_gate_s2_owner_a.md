# Plan-B seg400_460 Gate-S2 (Owner A)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400`
- Data: `data/selfcap_bar_8cam60f_seg400_460`
- Budget guard: `MAX_STEPS=200` only (no full600)

## Smoke200 commands

Baseline:
- `GPU=0 MAX_STEPS=200 DATA_DIR=data/selfcap_bar_8cam60f_seg400_460 RESULT_DIR=outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200 bash scripts/run_train_baseline_selfcap.sh`

Plan-B init:
- `GPU=0 MAX_STEPS=200 DATA_DIR=data/selfcap_bar_8cam60f_seg400_460 BASELINE_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init/keyframes_60frames_step5.npz PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg400_460/init_points_planb_step5.npz RESULT_DIR=outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200 bash scripts/run_train_planb_init_selfcap.sh`

## Artifact checks

- baseline: `stats/test_step0199.json`, `stats/throughput.json`, `videos/traj_4d_step199.mp4` present
- planb: `stats/test_step0199.json`, `stats/throughput.json`, `videos/traj_4d_step199.mp4` present
- training stability: no NaN/divergence in logs, run completed at step199

## Metrics (test@step199)

Baseline (`baseline_smoke200`):
- PSNR `12.5888776779`
- SSIM `0.2980958521`
- LPIPS `0.6276710629`
- tLPIPS `0.0851773545`

Plan-B (`planb_init_smoke200`):
- PSNR `12.7610082626`
- SSIM `0.3073078394`
- LPIPS `0.5838674903`
- tLPIPS `0.0352740064`

Delta (planb - baseline):
- `ΔPSNR = +0.1721305847`
- `ΔLPIPS = -0.0438035727` (improved)
- `ΔtLPIPS = -0.0499033481` (improved)
- relative `tLPIPS` improvement: `58.5876%`

## Gate-S2 decision

Condition 1:
- tLPIPS relative drop `58.5876% >= 5%`: PASS
- PSNR degradation check (`drop <= 0.2 dB`): PASS (`PSNR` is higher)

Condition 2:
- LPIPS drop `0.0438 >= 0.01`: PASS

Decision: **PASS** (both conditions satisfied).
