# Protocol Scoreboard
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`599`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v2/`

| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| planb_feat_v2_full600_lam0.005_start300_ramp200_every16 | 20.5725 | 0.7057 | 0.3515 | 0.0076 | - | - | - | - |
| planb_feat_v2_full600_lam0.005_warm100_ramp400 | 20.4106 | 0.7057 | 0.3530 | 0.0074 | - | - | - | - |

## 风险提示
- 无法判断：缺少 `ours_weak_600`、`control_weak_nocue_600`。

## 结论要点（自动生成）
- PSNR 最优：`planb_feat_v2_full600_lam0.005_start300_ramp200_every16` (20.5725)
- tLPIPS 最优：`planb_feat_v2_full600_lam0.005_warm100_ramp400` (0.0074)
- 风险提示：无法判断：缺少 `ours_weak_600`、`control_weak_nocue_600`。
