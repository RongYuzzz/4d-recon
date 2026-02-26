# Ablation Notes (Plan-B Defense v17, 2026-02-26)

本文件为 Plan-B 主线收口版（No-GPU 刷新），随 `scripts/pack_evidence.py` 打包。

## 协议与约束

- 协议固定：`docs/protocol.yaml` (`protocol_v1`)
- 不改 `data/`、不改帧段/相机划分/`global_scale`/`keyframe_step`
- feature-loss 主线冻结：不再新增 full600，仅保留失败归因材料

## Canonical 关键对比（test@step599）

| Run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 |

读法：Plan-B 在 canonical 上同时提升 PSNR/SSIM，并显著降低 LPIPS/tLPIPS。

## seg200_260 anti-cherrypick（test）

| Run | Step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.7162 | 0.3176 | 0.6349 | 0.0862 |
| planb_init_smoke200 | 199 | 12.9204 | 0.3206 | 0.5819 | 0.0338 |
| baseline_600 | 599 | 18.0468 | 0.6353 | 0.4138 | 0.0234 |
| control_weak_nocue_600 | 599 | 18.1969 | 0.6369 | 0.4157 | 0.0222 |
| planb_init_600 | 599 | 20.0417 | 0.6656 | 0.3534 | 0.0078 |

读法：在 seg2 切片中，Plan-B 的 smoke200 与 full600 都保持与 canonical 一致方向，支持 anti-cherrypick 防守。

## 写作口径（可直接复用）

- Plan-B 不改变协议分布项，只替换初始化速度来源（triangulation -> 3D velocity init）。
- Plan-B 解决的是 velocity prior 的质量/尺度/一致性不足或噪声过大，不是“速度为 0 已被证实”。
