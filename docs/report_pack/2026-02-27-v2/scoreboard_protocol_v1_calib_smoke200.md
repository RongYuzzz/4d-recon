# Smoke200 M1 Analysis
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`199`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v1_calib/`
- Baseline: `baseline_smoke200_l4d1e-3_dur0`

## M1 Table
| run | PSNR | tLPIPS | ΔPSNR | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200_l4d1e-2_dur0 | 12.6331 | 0.0875 | -0.0039 | -0.0002 | +0.0005 |
| baseline_smoke200_l4d1e-3_dur0 | 12.6370 | 0.0871 | +0.0000 | +0.0000 | +0.0000 |
| baseline_smoke200_l4d1e-4_dur0 | 12.6533 | 0.0873 | +0.0162 | +0.0032 | +0.0002 |

## Pareto Frontier
| run | PSNR | tLPIPS |
| --- | ---: | ---: |
| baseline_smoke200_l4d1e-4_dur0 | 12.6533 | 0.0873 |
| baseline_smoke200_l4d1e-3_dur0 | 12.6370 | 0.0871 |

## Recommendation
- 推荐 run：`baseline_smoke200_l4d1e-4_dur0` (PSNR=12.6533, tLPIPS=0.0873)
- 约束：PSNR >= 12.1370, tLPIPS <= 0.0971
