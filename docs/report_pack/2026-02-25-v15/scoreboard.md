# Protocol Scoreboard
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`599`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v1/`

| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 | +0.1603 | +0.0021 | -0.0015 | +0.0006 |
| feature_loss_v2_postfix_600 | 18.6752 | 0.6562 | 0.4219 | 0.0261 | -0.2744 | -0.0090 | +0.0172 | +0.0031 |

## 风险提示
- 未发现 `control_weak_nocue_600` 优于 `ours_weak_600` 的风险信号。

## 结论要点（占位）
- 结论要点 1：TODO
- 结论要点 2：TODO
- 结论要点 3：TODO
