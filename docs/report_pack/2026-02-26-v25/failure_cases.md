# Failure Cases (Plan-B + Negative Result Defense v25, 2026-02-26)

本文件用于答辩“失败分析”与“为何 pivot 合理”的统一口径。
v22 之后继续追加 seg600_660（或 fallback 的 seg300_360）防守位证据。
本次 v25 为 template hygiene 刷新（seg400_460/seg1800_1860）。

## Case 1: feature-loss v2 仍为负结果（主线已冻结）

- 可用证据：`feature_loss_v2_smoke200` / `feature_loss_v2_gated_smoke200` 指标显著弱于 baseline。
- 处理决策：不再追加 feature-loss full600，转入 No-GPU 最小归因链。
- 归因文档：`notes/feature_loss_v2_failure_attribution_owner_b.md` 与 `notes/feature_loss_failure_attribution_minpack.md`。

## Case 2: cue 注入路径存在负增益风险

- canonical 对照中，`control_weak_nocue_600` 在 LPIPS 上优于 `ours_weak_600`（见 scoreboard 风险提示）。
- 含义：弱融合/注入路径并非天然收益来源，存在方法边界。

## Case 3: Plan-B 叙事纠偏（必须遵守）

- 禁止口径：“零速陷阱已证实”。
- 正确口径：Plan-B 面向 **velocity prior 质量/尺度/一致性不足或噪声过大** 导致的动态重建不稳。

## Case 4: anti-cherrypick 防守位（seg200_260 + seg400_460）

- seg200_260 与 seg400_460 的 smoke200 证据方向与 canonical 一致：Plan-B 在 PSNR 提升同时降低 LPIPS/tLPIPS。
- 定位：正文以 canonical 为主结论，两段 seg 结果放附录作为“非 cherry-pick”防守。

## Case 5: 组件消融揭示“必要项”

- `planb_ablate_no_mutual_smoke200` 相对 default 出现一致退化（`PSNR -0.0534`, `LPIPS +0.0097`, `tLPIPS +0.0135`）。
- 结论：**mutual NN 是当前 Plan-B 收益的必要组件**；`no_drift` 与 `clip_p95` 更接近鲁棒性调节项。

## Case 6: 定性证据（side-by-side）

- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000000.jpg`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000030.jpg`
- `outputs/qualitative/planb_vs_baseline/frames/frame_000059.jpg`

以上文件不入库，但在存在时会被 evidence tar 自动收录。

## Case 7: feature-loss v2 梯度链检查（DONE）

- 证据文件：`outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv`
- 说明文档：`notes/feature_loss_v2_grad_chain_owner_a.md`、`notes/handoff_feature_loss_v2_grad_chain_owner_a.md`
- 结论口径：该项用于排除“实现无效/梯度链断”，不等价于“feature-loss 路线可行”。

## Case 8: Plan-B + weak（smoke200）补充结论

- cue 注入的负增益风险在 Plan-B 下仍存在（smoke200）。
