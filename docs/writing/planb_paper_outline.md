# Plan-B 论文/答辩写作骨架（v26）

## v26 写作冲刺入口（会议材料）
- 一页纸：`docs/writing/planb_onepager_v26.md`
- 讲稿大纲：`docs/writing/planb_talk_outline_v26.md`
- Q&A 卡片：`docs/writing/planb_qa_cards_v26.md`

## 摘要
- 结论：本文给出一条可复现的动态重建协议，并在固定预算下得到可辩护的 Plan-B 收益。证据：`docs/report_pack/2026-02-26-v26/metrics.csv`。
- 结论：主结论基于 canonical，且用 seg200_260/seg400_460/seg600_660/seg300_360/seg1800_1860 作为 anti-cherrypick 防守。证据：`docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`。
- 结论：feature-loss 负结果被收口为“机制归因链已闭环”，不是未排查状态。证据：`docs/report_pack/2026-02-26-v26/failure_cases.md`、`notes/feature_loss_failure_attribution_minpack.md`。

## 方法（Plan-B + mutual NN）
- 结论：Plan-B 的核心是初始化/先验修正，而非更改评测协议。证据：`docs/report_pack/2026-02-26-v26/ablation_notes.md`、`notes/handoff_planb_seg1800_1860_owner_a.md`。
- 结论：为排除“模板来自 canonical”的质疑，我们对 seg400_460 与 seg1800_1860 重做了 template hygiene：使用该 slice 自己的 baseline init（positions/colors/times/durations）作为模板，仅替换 velocities，并重跑 planb_init_smoke200；v26 以 re-template 后的结果为准。证据：`docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`。
- 结论：mutual NN 的写作口径是稳定器（stabilizer），主要作用于时序稳定性与退化风险控制；不宣称其为主要 PSNR 来源。证据：`docs/report_pack/2026-02-26-v26/metrics.csv`、`docs/report_pack/2026-02-26-v26/ablation_notes.md`。
- 结论：叙事口径统一为 velocity prior 质量/尺度/一致性不足或噪声过大。证据：`docs/report_pack/2026-02-26-v26/failure_cases.md`。

## 实验（主表 + anti-cherrypick）
- 结论：canonical 主表中，Plan-B 在 PSNR 提升同时降低 LPIPS/tLPIPS。证据：`docs/report_pack/2026-02-26-v26/scoreboard.md`。
- 结论：seg200_260/seg400_460/seg600_660/seg300_360/seg1800_1860 方向一致，支持“非 cherry-pick”防守。证据：`docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`、`notes/anti_cherrypick_seg1800_1860.md`。
- 结论：写作中正文只放 canonical 主表，seg 结果放附录作为稳健性支撑。证据：`docs/report_pack/2026-02-26-v26/metrics.csv`、`docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`。
- 结论：在 `planb_init` 框架下，cue 风险在 smoke200 仍需谨慎处理（收益幅度有限且 tLPIPS 未同向改善）。证据：`docs/report_pack/2026-02-26-v26/metrics.csv`、`docs/decisions/2026-02-26-planb-v26-freeze.md`。

## Scope 与 Limitations（冻结口径）
- Scope：本轮只声明“短预算（600 steps）下的收敛性与时序稳定性改进”，不声明高保真上限（high-fidelity ceiling）。
- Limitation 1：Feature Loss 与 Plan-B 正交，但受预算冻结（新增 full600 `N=0`）约束，未测 Plan-B + Feature Loss 组合，写为 future work。
- Limitation 2：feature-loss v2 以负结果边界材料保留，不再作为主线推进，不追加新训练。

## 负结果与失败归因（feature-loss v2）
- 结论：feature-loss v2 主线已冻结为负结果，不再追加 full600 训练。证据：`docs/report_pack/2026-02-26-v26/failure_cases.md`。
- 结论：梯度链检查已完成，可排除“loss 有值但不驱动参数”的实现断链解释。证据：`notes/feature_loss_v2_grad_chain_owner_a.md`。
- 结论：梯度链正常不等价于方案可行，仍归为优化对抗或方法边界。证据：`notes/feature_loss_failure_attribution_minpack.md`、`docs/report_pack/2026-02-26-v26/failure_cases.md`。

## 复现路径（答辩可直接引用）
- 报表与证据快照：`docs/report_pack/2026-02-26-v26/`、`notes/handoff_planb_seg1800_1860_owner_a.md`。
- 关键结论文稿：`notes/planb_verdict_writeup_owner_b.md`、`notes/anti_cherrypick_seg1800_1860.md`、`notes/planb_plus_weak_smoke200_owner_a.md`。
