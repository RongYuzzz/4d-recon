# Ablation Notes (Plan-B Defense v18, 2026-02-26)

本文件为 v18 收口版，围绕 Plan-B 主线证据（canonical + seg200_260）与 anti-cherrypick 防守位整理。

## 协议与约束

- 协议固定：`docs/protocol.yaml` (`protocol_v1`)
- 不改 `data/`、不改帧段/相机划分/`global_scale`/`keyframe_step`
- feature-loss 主线冻结：不再新增 full600，仅保留 No-GPU 归因材料

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

读法：在 seg2 切片中，Plan-B 的 smoke200 与 full600 均保持与 canonical 一致方向。

## seg400_460 anti-cherrypick（smoke200，test@step199）

| Run | Step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.5889 | 0.2981 | 0.6277 | 0.08518 |
| planb_init_smoke200 | 199 | 12.7610 | 0.3073 | 0.5839 | 0.03527 |

Delta（planb - baseline）：
- ΔPSNR `+0.1721`
- ΔLPIPS `-0.0438`
- ΔtLPIPS `-0.04990`（相对 `-58.59%`）

读法：该段仅补 smoke200（budget-neutral），但方向与 canonical/seg200_260 保持一致，可作为第三段 anti-cherrypick 辅证。

## 写作口径（可直接复用）

- Plan-B 不改变协议分布项，只替换初始化速度来源（triangulation -> 3D velocity init）。
- Plan-B 解决的是 velocity prior 的质量/尺度/一致性不足或噪声过大，不是“速度为 0 已被证实”。
