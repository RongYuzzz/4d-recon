# Plan-B Gate-B2 (Owner A)

- Date: 2026-02-26
- Run: `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600`

## Step 1: full600 (single run)

Command:
- `GPU=0 MAX_STEPS=600 PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600 bash scripts/run_train_planb_init_selfcap.sh`

Artifacts verified:
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/stats/test_step0599.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/stats/throughput.json`

## Step 2: quick compare vs baseline_600

Commands executed:
- `python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack`
- `python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md`
- Supplemental compare view for planb row visibility:
  - `python3 scripts/analyze_smoke200_m1.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md --step 599 --baseline_regex '^baseline_600$'`

Verification:
- `outputs/report_pack/metrics.csv` contains `planb_init_600` test@599.
- `outputs/report_pack/scoreboard.md` contains `planb_init_600` and `baseline_600`.

## Step 3: Gate-B2 Go/No-Go

Test metrics @599:
- baseline_600:
  - PSNR `18.9496269226`
  - LPIPS `0.4047809839`
  - tLPIPS `0.0229585823`
- planb_init_600:
  - PSNR `20.4488086700`
  - LPIPS `0.3496737480`
  - tLPIPS `0.0071958611`

Delta (planb - baseline):
- `ΔPSNR = +1.4991817474 dB`
- `ΔLPIPS = -0.0551072359`
- `ΔtLPIPS = -0.0157627212` (relative `-68.66%`)

Decision by plan criteria:
- Go condition requires tLPIPS ≤ `-5%` vs baseline and PSNR not worse than `-0.2dB`.
- Observed: tLPIPS improves by `-68.66%`, PSNR improves by `+1.499dB`, and training remains stable.

Decision: **Go**.
