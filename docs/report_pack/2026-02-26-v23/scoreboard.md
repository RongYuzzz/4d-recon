# Protocol Scoreboard
- Source: `/root/projects/4d-recon/outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`599`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v1/`

| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| ours_weak_600 | 19.0194 | 0.6661 | 0.4037 | 0.0231 | +0.0698 | +0.0009 | -0.0011 | +0.0001 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 | +0.1603 | +0.0021 | -0.0015 | +0.0006 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 | +1.4992 | +0.0418 | -0.0551 | -0.0158 |
| feature_loss_v1_600 | 16.0347 | 0.6061 | 0.4927 | 0.0443 | -2.9149 | -0.0592 | +0.0879 | +0.0213 |
| feature_loss_v1_retry_lam0.005_s200_600 | 19.0555 | 0.6644 | 0.4054 | 0.0239 | +0.1059 | -0.0008 | +0.0006 | +0.0010 |
| feature_loss_v2_postfix_600 | 18.6752 | 0.6562 | 0.4219 | 0.0261 | -0.2744 | -0.0090 | +0.0172 | +0.0031 |
| ours_strong_600 | 19.0236 | 0.6660 | 0.4094 | 0.0233 | +0.0739 | +0.0008 | +0.0046 | +0.0003 |
| ours_strong_v2_600 | 18.8095 | 0.6629 | 0.4080 | 0.0247 | -0.1401 | -0.0024 | +0.0032 | +0.0018 |
| ours_strong_v3_gate1_detach0_predpred_600 | 18.9491 | 0.6652 | 0.4072 | 0.0228 | -0.0006 | -0.0001 | +0.0025 | -0.0002 |

## 风险提示
- <span style='color:red'>`control_weak_nocue_600` 的 LPIPS 优于 `ours_weak_600`，提示当前 cue/注入方式可能产生负增益。</span>

## 结论要点（自动生成）
- PSNR 最优：`planb_init_600` (20.4488)
- tLPIPS 最优：`planb_init_600` (0.0072)
- 风险提示：发现 `control_weak_nocue_600` 相对 `ours_weak_600` 的潜在负增益风险。
