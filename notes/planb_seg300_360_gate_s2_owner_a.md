# Plan-B seg300_360 Gate-S2 (Owner A)

- Date: 2026-02-26
- Slice data: `/root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360`
- Compare: `baseline_smoke200` vs `planb_init_smoke200`

## Commands

Baseline:
- `GPU=0 MAX_STEPS=200 DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360 RESULT_DIR=/root/projects/4d-recon/outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200 bash scripts/run_train_baseline_selfcap.sh`

Plan-B init:
- `GPU=0 MAX_STEPS=200 DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360 PLANB_INIT_NPZ=/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/init_points_planb_step5.npz RESULT_DIR=/root/projects/4d-recon/outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200 bash scripts/run_train_planb_init_selfcap.sh`

## Artifact checks

- baseline `stats/test_step0199.json`: PASS
- baseline `stats/throughput.json`: PASS
- baseline `videos/traj_4d_step199.mp4`: PASS
- planb `stats/test_step0199.json`: PASS
- planb `stats/throughput.json`: PASS
- planb `videos/traj_4d_step199.mp4`: PASS

## Metrics (test@step199)

- baseline: `PSNR 12.7534875870 / LPIPS 0.6217724085 / tLPIPS 0.0846709535`
- planb: `PSNR 12.9346237183 / LPIPS 0.5720292926 / tLPIPS 0.0329684690`
- deltas (planb - baseline): `ΔPSNR +0.1811361313 / ΔLPIPS -0.0497431159 / ΔtLPIPS -0.0517024845`
- `tLPIPS` relative improvement: `61.0628%`

## Gate-S2 decision

- 条件1（`tLPIPS` 相对下降 ≥5%，且 PSNR 不劣化超过 0.2 dB）：PASS
- 条件2（`LPIPS` 下降 ≥0.01 且训练稳定）：PASS
- **总体：PASS**

## Conclusion

seg300_360 在 smoke200 下与既有切片同向：Plan-B init 同时改善 LPIPS 与 tLPIPS，且 PSNR 无惩罚。
