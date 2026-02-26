# Plan-B v26 Table-1 Extract (Owner A)

- Date: 2026-02-26
- Source of truth: `docs/report_pack/2026-02-26-v26/metrics.csv`
- Definition: `Δ = planb - baseline`
- Filter used: `stage=test`, `step=599`, full600 runs only

## canonical (protocol_v1/selfcap_bar_8cam60f)

| Variant | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 |
| Δ (planb-baseline) | +1.4992 | +0.0418 | -0.0551 | -0.0158 |

## seg200_260 (protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260)

| Variant | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.0468 | 0.6353 | 0.4138 | 0.0234 |
| planb_init_600 | 20.0417 | 0.6656 | 0.3534 | 0.0078 |
| Δ (planb-baseline) | +1.9950 | +0.0303 | -0.0604 | -0.0156 |

