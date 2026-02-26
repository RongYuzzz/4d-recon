# Plan-B Gate-B1 (Owner A)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb`

## Step 1: Plan-B init generation

Command:
- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/init_velocity_from_points.py --data_dir data/selfcap_bar_8cam60f --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz --frame_start 0 --frame_end_exclusive 60 --keyframe_step 5 --out_dir outputs/plan_b/selfcap_bar_8cam60f`

Artifacts:
- `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`

Key stats (`velocity_stats.json`):
- `match_ratio_over_eligible`: `0.6029265087`
- `match_ratio_over_all`: `0.5539898004`
- `v_valid mean/max (m/frame)`: `0.0018724554 / 0.0108813839`
- `ratio(||v||<1e-4)` over valid: `0.0028414620`
- `ratio(||v||<1e-4)` over all: `0.4475843405`
- `clip_quantile`: `0.99`, `n_clipped`: `514`

## Step 2: baseline_smoke200

Run:
- `GPU=0 MAX_STEPS=200 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window bash scripts/run_train_baseline_selfcap.sh`

Artifacts verified:
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window/videos/traj_4d_step199.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window/stats/throughput.json`

Metrics (test@199):
- PSNR `12.6349887848`
- LPIPS `0.6297485828`
- tLPIPS `0.0877432004`

## Step 3: planb_init_smoke200

Run:
- `GPU=0 MAX_STEPS=200 PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200 bash scripts/run_train_planb_init_selfcap.sh`

Artifacts verified:
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/videos/traj_4d_step199.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/throughput.json`

Metrics (test@199):
- PSNR `12.8382835388`
- LPIPS `0.5795553327`
- tLPIPS `0.0335242674`

## Step 4: smoke200 compare table

Commands:
- `python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack`
- `python3 scripts/analyze_smoke200_m1.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard_smoke200.md --baseline_regex '^baseline_smoke200_planb_window$'`

Check:
- `outputs/report_pack/scoreboard_smoke200.md` includes `planb_init_smoke200`

## Gate-B1 decision

No direct No-Go condition triggered:
- No training instability / NaN / divergence observed.
- `match_ratio_over_eligible` is high (`0.603`, not near `<0.01`).
- Valid-velocity near-zero ratio is low (`0.00284`, not near `1.0`).
- smoke200 metrics improve vs baseline (PSNR +0.2033 dB, LPIPS -0.0502, tLPIPS -0.0542).

Decision: **Gate-B1 PASS, proceed to Gate-B2 full600 (single run).**
