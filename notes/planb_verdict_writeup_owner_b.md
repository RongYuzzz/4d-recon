# Plan-B Verdict Writeup (Owner B, 2026-02-26)

## Go/No-Go（48h 口径）

- 结论：**Plan-B = Go（在 48h timebox 内形成可辩护正向证据）**。
- 依据：`planb_init_600` 相对 canonical baseline/control 在 step599 呈现一致提升：PSNR/SSIM 提升，LPIPS/tLPIPS 下降。
- 约束保留：`protocol_v1` 不变，`data/` 不变，不新增 feature-loss full600。

## 四行关键对比（test@step599）

| Slice | Run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | ---: | ---: | ---: | ---: |
| canonical | baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| canonical | control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| canonical (Plan-B) | planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 |
| seg200_260 | control_weak_nocue_600 | 18.1969 | 0.6369 | 0.4157 | 0.0222 |

## 答辩一句话（防守口径）

Plan-B 解决的不是“速度是否为 0”，而是 **velocity prior 的质量/尺度/一致性不足或噪声过大** 导致的动态重建不稳；triangulation 的跨帧 3D 差分初始化提供了更物理一致的 motion 起点。
