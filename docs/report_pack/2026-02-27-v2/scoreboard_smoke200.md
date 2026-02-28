# Protocol Scoreboard
- Source: `outputs/report_pack/metrics.csv`
- Filter: stage=`test`, step=`199`, contains=`selfcap_bar_8cam60f`, prefix=`outputs/protocol_v2/`
- Delta baseline: `planb_init_smoke200`

| run | PSNR | SSIM | LPIPS | tLPIPS | ΔPSNR | ΔSSIM | ΔLPIPS | ΔtLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16 | 12.8394 | 0.3108 | 0.5800 | 0.0336 | +0.0011 | -0.0002 | +0.0004 | +0.0001 |
| planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16 | 12.8371 | 0.3109 | 0.5795 | 0.0338 | -0.0012 | -0.0001 | -0.0000 | +0.0003 |
| planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16_s43_gpu1 | 12.8331 | 0.3092 | 0.5822 | 0.0343 | -0.0052 | -0.0018 | +0.0026 | +0.0007 |
| planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16 | 12.8371 | 0.3107 | 0.5797 | 0.0337 | -0.0012 | -0.0003 | +0.0002 | +0.0002 |
| planb_feat_v2_smoke200_framediff_p0.10_lam0.002_warm100 | 12.8281 | 0.3107 | 0.5797 | 0.0339 | -0.0102 | -0.0003 | +0.0002 | +0.0004 |
| planb_feat_v2_smoke200_framediff_p0.10_lam0.005_warm100 | 12.8155 | 0.3101 | 0.5805 | 0.0338 | -0.0228 | -0.0008 | +0.0010 | +0.0003 |
| planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16 | 12.8395 | 0.3109 | 0.5798 | 0.0338 | +0.0012 | -0.0001 | +0.0002 | +0.0003 |
| planb_feat_v2_smoke200_lam0.002_start200_ramp50_every16_s42_gpu1 | 12.8395 | 0.3109 | 0.5795 | 0.0338 | +0.0012 | -0.0000 | -0.0000 | +0.0003 |
| planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100 | 12.8276 | 0.3105 | 0.5800 | 0.0343 | -0.0107 | -0.0005 | +0.0005 | +0.0007 |
| planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16 | 12.8365 | 0.3107 | 0.5794 | 0.0338 | -0.0018 | -0.0003 | -0.0002 | +0.0003 |
| planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf | 12.8384 | 0.3109 | 0.5789 | 0.0336 | +0.0001 | -0.0001 | -0.0006 | +0.0001 |
| planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s43_gpu1 | 12.8331 | 0.3090 | 0.5824 | 0.0343 | -0.0052 | -0.0020 | +0.0028 | +0.0008 |
| planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0 | 12.8403 | 0.3112 | 0.5793 | 0.0339 | +0.0020 | +0.0003 | -0.0003 | +0.0004 |
| planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s42_gpu1 | 12.8380 | 0.3109 | 0.5800 | 0.0338 | -0.0003 | -0.0001 | +0.0004 | +0.0002 |
| planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s43_gpu1 | 12.8258 | 0.3090 | 0.5822 | 0.0344 | -0.0125 | -0.0020 | +0.0026 | +0.0009 |
| planb_feat_v2_smoke200_lam0.005_start200_ramp50_every16_s42_gpu1 | 12.8394 | 0.3109 | 0.5791 | 0.0336 | +0.0011 | -0.0001 | -0.0004 | +0.0001 |
| planb_feat_v2_smoke200_lam0.005_warm100 | 12.8345 | 0.3106 | 0.5802 | 0.0337 | -0.0038 | -0.0004 | +0.0007 | +0.0002 |
| planb_feat_v2_smoke200_lam0.01_warm100 | 12.8224 | 0.3102 | 0.5801 | 0.0336 | -0.0158 | -0.0008 | +0.0005 | +0.0001 |
| planb_feat_v2_smoke200_lam0_sanity | 12.8409 | 0.3107 | 0.5792 | 0.0337 | +0.0026 | -0.0003 | -0.0004 | +0.0002 |
| planb_feat_v2_smoke200_lam0_sanity_s42_gpu1 | 12.8368 | 0.3106 | 0.5801 | 0.0334 | -0.0015 | -0.0004 | +0.0005 | -0.0001 |
| planb_feat_v2_smoke200_lam0_sanity_s43_gpu1 | 12.8364 | 0.3091 | 0.5820 | 0.0341 | -0.0018 | -0.0018 | +0.0024 | +0.0006 |

## 风险提示
- 无法判断：缺少 `ours_weak_600`、`control_weak_nocue_600`。

## 结论要点（自动生成）
- PSNR 最优：`planb_feat_v2_smoke200_lam0_sanity` (12.8409)
- tLPIPS 最优：`planb_feat_v2_smoke200_lam0_sanity_s42_gpu1` (0.0334)
- 风险提示：无法判断：缺少 `ours_weak_600`、`control_weak_nocue_600`。
