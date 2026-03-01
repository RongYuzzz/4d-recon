# Protocol v1 Convergecheck
- Source: raw stats JSON (`step=1999`)
- Runs: `baseline_long5k_dur0` vs `planb_init_long5k_dur0`

| run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_long5k_dur0 | 22.9387 | 0.7501 | 0.3120 | 0.0070 |
| planb_init_long5k_dur0 | 23.7671 | 0.7690 | 0.2778 | 0.0033 |

| delta (planb - baseline) | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: |
| values | 0.8284 | 0.0189 | -0.0342 | -0.0037 |

Interpretation: positive ΔPSNR/ΔSSIM and negative ΔLPIPS/ΔtLPIPS favor planb.
