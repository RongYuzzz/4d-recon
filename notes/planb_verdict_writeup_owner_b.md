# Plan-B Verdict Writeup (Owner B, 2026-02-26, v26 freeze)

## Go/No-Go（冻结口径）
- 结论：**Plan-B = Go**。
- 冻结：`feature-loss v2 = No-Go`，`Plan-B + weak = No-Go`。
- 预算：新增 full600 `N=0`，当前只做 No-GPU 写作与证据整理。

## Template Hygiene 声明（防守句）
为排除“模板来自 canonical”的质疑，我们对 seg400_460 与 seg1800_1860 已按同 slice baseline init（positions/colors/times/durations）重模板，仅替换 velocities 并重跑 `planb_init_smoke200`；v26 口径以重模板结果为准。

## 三段式写作口径（可直接贴到 slides）

### 1) Plan-B 一句话定义
Plan-B 是“物理一致初始化修正”：以 triangulation 的跨帧 3D 差分初始化 motion，仅替换初始化速度先验，不改协议与预算口径。

### 2) Canonical 主结论（test@step599）
| Run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 |
| feature_loss_v2_postfix_600 | 18.6752 | 0.6562 | 0.4219 | 0.0261 |

结论：`planb_init_600` 相对 `baseline_600` 同时提升 PSNR/SSIM 并降低 LPIPS/tLPIPS；`feature_loss_v2_postfix_600` 三项退化，主线已冻结。

### 3) anti-cherrypick 防守位（seg200_260 full600 + 多切片 smoke200）
| Slice | 对比 | ΔPSNR | ΔLPIPS | ΔtLPIPS |
| --- | --- | ---: | ---: | ---: |
| seg200_260 (full600) | planb_init_600 - baseline_600 | +1.9950 | -0.0604 | -0.0156 |
| seg300_360 (smoke200) | planb_init_smoke200 - baseline_smoke200 | +0.1811 | -0.0497 | -0.0517 |
| seg400_460 (smoke200) | planb_init_smoke200 - baseline_smoke200 | +0.1845 | -0.0481 | -0.0516 |
| seg600_660 (smoke200) | planb_init_smoke200 - baseline_smoke200 | +0.1905 | -0.0488 | -0.0525 |
| seg1800_1860 (smoke200) | planb_init_smoke200 - baseline_smoke200 | +0.1799 | -0.0489 | -0.0549 |

用法：正文只放 canonical + seg200_260 full600；其余 smoke200 放附录做 anti-cherrypick 防守。

## Mutual NN 统一口径（修订）
- 统一表述：**Mutual NN 是 stabilizer（稳定器）**。
- 作用定位：主要体现在时序稳定性与退化风险控制，不宣称其是主要 PSNR 来源。
- 讲法：主结论由 Plan-B 整体收益承载，组件结论放附录消融支撑。

## Plan-B + weak（No-Go 口径）
- canonical 风险：`control_weak_nocue_600` 的 LPIPS（0.4033）优于 `ours_weak_600`（0.4037）。
- Plan-B smoke200 风险：`planb_ours_weak_smoke200_w0.3_end200` 虽 LPIPS 略优于 `planb_init_smoke200`（0.5792 vs 0.5796），但 tLPIPS 变差（0.0338 vs 0.0335）。
- 结论：不满足“同向改善”准入标准，在 `N=0` 冻结期下不申请新增 full600。

## 答辩一句话（严格口径）
Plan-B 解决的不是“速度是否为 0”，而是 **velocity prior 的质量/尺度/一致性不足或噪声过大** 导致的动态重建不稳。

## 统一证据入口（v26）
- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`
