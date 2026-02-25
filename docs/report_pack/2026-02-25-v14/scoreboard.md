# Protocol Scoreboard
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`599`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v1/`

| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 | +0.1603 | +0.0021 | -0.0015 | +0.0006 |
| feature_loss_v2_600 | 15.9437 | 0.6065 | 0.4996 | 0.0462 | -3.0059 | -0.0588 | +0.0948 | +0.0232 |
| feature_loss_v2_gated_600 | 15.1714 | 0.5921 | 0.5140 | 0.0507 | -3.7782 | -0.0732 | +0.1092 | +0.0278 |

## 风险提示
- 未发现 `control_weak_nocue_600` 优于 `ours_weak_600` 的风险信号。

## 结论要点（占位）
- 结论要点 1：TODO
- 结论要点 2：TODO
- 结论要点 3：TODO
