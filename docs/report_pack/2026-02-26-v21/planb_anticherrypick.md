# Plan-B Anti-Cherrypick Summary
- Source: `outputs/report_pack/metrics.csv`

## Canonical
| run | step | PSNR | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 599 | 18.9496 | 0.4048 | 0.0230 |
| planb_init_600 | 599 | 20.4488 | 0.3497 | 0.0072 |
- Delta (planb - baseline): ΔPSNR=+1.4992, ΔLPIPS=-0.0551, ΔtLPIPS=-0.0158

## seg200_260
| run | step | PSNR | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 599 | 18.0468 | 0.4138 | 0.0234 |
| planb_init_600 | 599 | 20.0417 | 0.3534 | 0.0078 |
- Delta (planb - baseline): ΔPSNR=+1.9950, ΔLPIPS=-0.0604, ΔtLPIPS=-0.0156

## seg400_460
| run | step | PSNR | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.5889 | 0.6277 | 0.0852 |
| planb_init_smoke200 | 199 | 12.7610 | 0.5839 | 0.0353 |
- Delta (planb - baseline): ΔPSNR=+0.1721, ΔLPIPS=-0.0438, ΔtLPIPS=-0.0499
