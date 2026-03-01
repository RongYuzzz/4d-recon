# Protocol Scoreboard
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`599`, contains=`selfcap_bar_8cam60f_seg300_360`, prefix=`outputs/protocol_v1_seg300_360/`

| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_600 | 19.1647 | 0.6490 | 0.3963 | 0.0217 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| planb_init_600 | 20.7071 | 0.6905 | 0.3448 | 0.0076 | +1.5424 | +0.0415 | -0.0515 | -0.0141 |

## 风险提示
- 无法判断：缺少 `ours_weak_600`、`control_weak_nocue_600`。

## 结论要点（自动生成）
- PSNR 最优：`planb_init_600` (20.7071)
- tLPIPS 最优：`planb_init_600` (0.0076)
- 风险提示：无法判断：缺少 `ours_weak_600`、`control_weak_nocue_600`。
