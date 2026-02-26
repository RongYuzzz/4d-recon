# Failure Cases (Plan-B + Negative Result Defense v18, 2026-02-26)

本文件用于答辩“失败分析”与“为何 pivot 合理”的统一口径。

## Case 1: feature-loss v2 仍为负结果（主线已冻结）

- 可用证据：`feature_loss_v2_smoke200` / `feature_loss_v2_gated_smoke200` 指标显著弱于 baseline。
- 处理决策：不再追加 feature-loss full600，转入 No-GPU 最小归因链。
- 归因文档：`notes/feature_loss_v2_failure_attribution_owner_b.md`。

## Case 2: cue 注入路径存在负增益风险

- canonical 对照中，`control_weak_nocue_600` 在 LPIPS 上优于 `ours_weak_600`（见 scoreboard 风险提示）。
- 含义：弱融合/注入路径并非天然收益来源，存在方法边界。

## Case 3: Plan-B 叙事纠偏（必须遵守）

- 禁止口径：“零速陷阱已证实”。
- 正确口径：Plan-B 面向 **velocity prior 质量/尺度/一致性不足或噪声过大** 导致的动态重建不稳。

## Case 4: anti-cherrypick 防守位

- seg200_260 已给出 baseline/control/planb 的 smoke200 + full600 证据，方向与 canonical 一致。
- seg400_460 已补 smoke200（budget-neutral），方向与 canonical/seg200_260 一致（见 `notes/anti_cherrypick_seg400_460.md`）。

## Case 5: 定性证据（side-by-side）

- 新增可复用定性资产：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- 对应关键帧：`frame_000000.jpg`、`frame_000030.jpg`、`frame_000059.jpg`
- 以上文件不入库，但可被 evidence tar 自动收录（若存在）。
