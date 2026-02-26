# Plan-B Anti-Cherrypick Summary
- Source: `/root/projects/4d-recon/outputs/report_pack/metrics.csv`

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
| planb_init_smoke200 | 199 | 12.7733 | 0.5796 | 0.0336 |
- Delta (planb - baseline): ΔPSNR=+0.1845, ΔLPIPS=-0.0481, ΔtLPIPS=-0.0516

## seg600_660
| run | step | PSNR | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.5847 | 0.6268 | 0.0864 |
| planb_init_smoke200 | 199 | 12.7752 | 0.5779 | 0.0339 |
- Delta (planb - baseline): ΔPSNR=+0.1905, ΔLPIPS=-0.0488, ΔtLPIPS=-0.0525

## seg300_360
| run | step | PSNR | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.7535 | 0.6218 | 0.0847 |
| planb_init_smoke200 | 199 | 12.9346 | 0.5720 | 0.0330 |
- Delta (planb - baseline): ΔPSNR=+0.1811, ΔLPIPS=-0.0497, ΔtLPIPS=-0.0517

## seg1800_1860
| run | step | PSNR | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.5796 | 0.6290 | 0.0888 |
| planb_init_smoke200 | 199 | 12.7595 | 0.5801 | 0.0340 |
- Delta (planb - baseline): ΔPSNR=+0.1799, ΔLPIPS=-0.0489, ΔtLPIPS=-0.0549
