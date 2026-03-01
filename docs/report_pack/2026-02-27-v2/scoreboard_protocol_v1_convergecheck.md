# Protocol v1 Convergecheck
- Source: raw stats JSON (`step=599`)
- Runs: `baseline_long5k_dur0` vs `planb_init_long5k_dur0`

| run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_long5k_dur0 | 18.6148 | 0.6539 | 0.4499 | 0.0253 |
| planb_init_long5k_dur0 | 19.8499 | 0.6808 | 0.4199 | 0.0130 |

| delta (planb - baseline) | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: |
| values | 1.2351 | 0.0269 | -0.0300 | -0.0123 |

Interpretation: positive ΔPSNR/ΔSSIM and negative ΔLPIPS/ΔtLPIPS favor planb.
