# Failure Cases (Plan-B + Negative Result Defense v17, 2026-02-26)

本文件用于答辩“失败分析”与“为何 pivot 合理”的统一口径。

## Case 1: feature-loss v2 仍为负结果（主线已冻结）

- 可用证据：`feature_loss_v2_smoke200` / `feature_loss_v2_gated_smoke200` 指标明显弱于 baseline。
- 处理决策：不再烧 feature-loss full600，转入 No-GPU 最小归因包。
- 归因文档：`notes/feature_loss_v2_failure_attribution_owner_b.md`。

## Case 2: cue 注入路径存在负增益风险

- canonical 对照中，`control_weak_nocue_600` 在 LPIPS 上优于 `ours_weak_600`（见 scoreboard 风险提示）。
- 含义：弱融合/注入路径并非天然收益来源，存在方法边界。

## Case 3: Plan-B 叙事纠偏（必须遵守）

- 禁止口径：“零速陷阱已证实”。
- 正确口径：Plan-B 面向 **velocity prior 质量/尺度/一致性不足或噪声过大** 导致的动态重建不稳。

## Case 4: anti-cherrypick 防守位（seg200_260）

- seg2 smoke200 与 full600 已提供 baseline/control/planb 三角关系。
- 结论方向与 canonical 一致：Plan-B 指标改善不依赖单一切片。
- 用法：正文给 canonical 主结论，seg2 作为附录防守证据位。
