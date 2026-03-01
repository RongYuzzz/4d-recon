# Protocol v1 Baseline Calibration (smoke200)

Date: 2026-03-01
Scope: `selfcap_bar_8cam60f`, stage=`test`, step=`199`, dur0

## Runs and metrics

| run | lambda_4d_reg | lambda_duration_reg | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_l4d1e-4_dur0` | 1e-4 | 0 | 12.6533 | 0.3066 | 0.6332 | 0.0873 |
| `outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_l4d1e-3_dur0` | 1e-3 | 0 | 12.6370 | 0.3068 | 0.6299 | 0.0871 |
| `outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_l4d1e-2_dur0` | 1e-2 | 0 | 12.6331 | 0.3066 | 0.6297 | 0.0875 |

## Decision

Chosen closeout `L4D = 1e-4`.

Rationale: this point has the highest PSNR in smoke200 and remains on the PSNR/tLPIPS Pareto set; tLPIPS change vs `1e-3` is minor for this calibration stage.

All decisive comparisons use dur0 + L4D for fairness.
