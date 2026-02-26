# Plan-B Verdict Writeup (Owner B, 2026-02-26)

## Go/No-Go（48h 口径）

- 结论：**Plan-B = Go**。
- 原则：仅替换 init velocities（triangulation -> 3D velocity init），不改 `protocol_v1` 与数据分布项。
- 约束：feature-loss 主线冻结，不再新增 full600。

## 三段式写作口径（可直接贴到 slides）

### 1) Plan-B 一句话定义

Plan-B 是“物理一致初始化修正”：以 triangulation 的跨帧 3D 差分初始化 motion，仅替换初始化速度先验，不改协议与训练预算口径。

### 2) Canonical 主结论（test@step599）

| Run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 |

结论：Plan-B 在 canonical 上同时提升 PSNR/SSIM，并显著降低 LPIPS/tLPIPS（相对 baseline，tLPIPS 约下降 0.0158）。

### 3) anti-cherrypick 防守位（seg200_260）

| Run | Step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_600 | 599 | 18.0468 | 0.6353 | 0.4138 | 0.0234 |
| control_weak_nocue_600 | 599 | 18.1969 | 0.6369 | 0.4157 | 0.0222 |
| planb_init_600 | 599 | 20.0417 | 0.6656 | 0.3534 | 0.0078 |

用法：正文以 canonical 为主结论，seg2 结果放附录作为 anti-cherrypick 防守证据。

### 4) seg400_460 smoke200（budget-neutral 防守位）

说明：seg400_460 仅补 **smoke200（test@step199）**，不新增 full600（budget-neutral）。

| Run | Step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.5889 | 0.2981 | 0.6277 | 0.08518 |
| planb_init_smoke200 | 199 | 12.7610 | 0.3073 | 0.5839 | 0.03527 |

结论：与 canonical/seg200_260 同向（PSNR 提升、LPIPS 下降、tLPIPS 大幅下降），可作为第三段 anti-cherrypick 防守位。

### 5) 预算纪律（必须写明）

- 现阶段 full600 预算已用尽；后续若需要继续跑 full600，必须先新增决议（扩预算）后再执行。
- 在无新决议前，仅允许 No-GPU 诊断、写作与证据链刷新，不新增训练预算。

## 答辩一句话（严格口径）

Plan-B 解决的不是“速度是否为 0”，而是 **velocity prior 的质量/尺度/一致性不足或噪声过大** 导致的动态重建不稳。
