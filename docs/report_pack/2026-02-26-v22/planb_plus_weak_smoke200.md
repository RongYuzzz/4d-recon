# Smoke200 M1 Analysis
- Source: `/root/projects/4d-recon/outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`199`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v1/`
- Baseline: `planb_init_smoke200`

## M1 Table
| run | PSNR | tLPIPS | ΔPSNR | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200_planb_window | 12.6350 | 0.0877 | -0.2033 | +0.0502 | +0.0542 |
| feature_loss_v1_sanity200 | 12.4811 | 0.0798 | -0.3571 | +0.0447 | +0.0463 |
| feature_loss_v2_gated_smoke200 | 12.5289 | 0.0813 | -0.3094 | +0.0444 | +0.0478 |
| feature_loss_v2_smoke200 | 12.5040 | 0.0807 | -0.3342 | +0.0460 | +0.0472 |
| planb_ablate_clip_p95_smoke200 | 12.8411 | 0.0329 | +0.0028 | -0.0005 | -0.0006 |
| planb_ablate_no_drift_smoke200 | 12.8481 | 0.0341 | +0.0098 | -0.0002 | +0.0005 |
| planb_ablate_no_mutual_smoke200 | 12.7849 | 0.0470 | -0.0534 | +0.0097 | +0.0135 |
| planb_control_weak_nocue_smoke200 | 12.8384 | 0.0340 | +0.0001 | +0.0002 | +0.0005 |
| planb_init_smoke200 | 12.8383 | 0.0335 | +0.0000 | +0.0000 | +0.0000 |
| planb_ours_weak_smoke200_w0.3_end200 | 12.8439 | 0.0338 | +0.0056 | -0.0003 | +0.0002 |

## Pareto Frontier
| run | PSNR | tLPIPS |
| --- | ---: | ---: |
| planb_ablate_no_drift_smoke200 | 12.8481 | 0.0341 |
| planb_ours_weak_smoke200_w0.3_end200 | 12.8439 | 0.0338 |
| planb_ablate_clip_p95_smoke200 | 12.8411 | 0.0329 |

## Recommendation
- 推荐 run：`planb_ablate_no_drift_smoke200` (PSNR=12.8481, tLPIPS=0.0341)
- 约束：PSNR >= 12.3383, tLPIPS <= 0.0435
