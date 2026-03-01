# Protocol v1 Convergecheck
- Source: raw stats JSON (`step=4999`)
- Runs: `baseline_long5k_dur0` vs `planb_init_long5k_dur0`

| run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_long5k_dur0 | 24.5499 | 0.8140 | 0.2169 | 0.0043 |
| planb_init_long5k_dur0 | 25.2990 | 0.8239 | 0.1872 | 0.0020 |

| delta (planb - baseline) | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: |
| values | 0.7491 | 0.0099 | -0.0297 | -0.0023 |

Interpretation: positive ΔPSNR/ΔSSIM and negative ΔLPIPS/ΔtLPIPS favor planb.
