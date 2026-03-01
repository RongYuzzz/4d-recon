# Smoke200 M1 Analysis
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`599`, contains=`_dur0`, prefix=`outputs/protocol_v1_seg300_360/`
- Baseline: `baseline_600_dur0`

## M1 Table
| run | PSNR | tLPIPS | ΔPSNR | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_600_dur0 | 19.2621 | 0.0216 | +0.0000 | +0.0000 | +0.0000 |
| planb_init_600_dur0 | 20.5168 | 0.0078 | +1.2546 | -0.0525 | -0.0137 |

## Pareto Frontier
| run | PSNR | tLPIPS |
| --- | ---: | ---: |
| planb_init_600_dur0 | 20.5168 | 0.0078 |

## Recommendation
- 推荐 run：`planb_init_600_dur0` (PSNR=20.5168, tLPIPS=0.0078)
- 约束：PSNR >= 18.7621, tLPIPS <= 0.0316
