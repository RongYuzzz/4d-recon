# Plan-B 论文/答辩写作骨架（v22）

## 摘要
- 结论：本文给出一条可复现的动态重建协议，并在固定预算下得到可辩护的 Plan-B 收益。证据：`docs/protocol.yaml`、`docs/report_pack/2026-02-26-v22/metrics.csv`。
- 结论：主结论基于 canonical，且用 seg200_260/seg400_460 作为 anti-cherrypick 防守。证据：`docs/report_pack/2026-02-26-v22/planb_anticherrypick.md`。
- 结论：feature-loss 负结果被收口为“机制归因链已闭环”，不是未排查状态。证据：`docs/report_pack/2026-02-26-v22/failure_cases.md`、`notes/feature_loss_failure_attribution_minpack.md`。

## 方法（Plan-B + mutual NN）
- 结论：Plan-B 的核心是初始化/先验修正，而非更改评测协议。证据：`docs/decisions/2026-02-26-planb-pivot.md`、`docs/protocol.yaml`。
- 结论：mutual NN 是当前收益必要组件，去除后指标一致退化。证据：`docs/report_pack/2026-02-26-v22/ablation_notes.md`。
- 结论：叙事口径统一为 velocity prior 质量/尺度/一致性不足或噪声过大。证据：`docs/report_pack/2026-02-26-v22/failure_cases.md`。

## 实验（主表 + anti-cherrypick）
- 结论：canonical 主表中，Plan-B 在 PSNR 提升同时降低 LPIPS/tLPIPS。证据：`docs/report_pack/2026-02-26-v22/scoreboard.md`。
- 结论：seg200_260 与 seg400_460 方向一致，支持“非 cherry-pick”防守。证据：`docs/report_pack/2026-02-26-v22/planb_anticherrypick.md`。
- 结论：写作中正文只放 canonical 主表，seg 结果放附录作为稳健性支撑。证据：`docs/report_pack/2026-02-26-v22/metrics.csv`、`docs/report_pack/2026-02-26-v22/planb_anticherrypick.md`。
- 结论：在 `planb_init` 框架下，cue 风险在 smoke200 仍需谨慎处理（收益幅度有限且 tLPIPS 未同向改善）。证据：`docs/report_pack/2026-02-26-v22/planb_plus_weak_smoke200.md`、`notes/planb_plus_weak_smoke200_owner_a.md`。

## 负结果与失败归因（feature-loss v2）
- 结论：feature-loss v2 主线已冻结为负结果，不再追加 full600 训练。证据：`docs/report_pack/2026-02-26-v22/failure_cases.md`。
- 结论：梯度链检查已完成，可排除“loss 有值但不驱动参数”的实现断链解释。证据：`outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv`、`notes/feature_loss_v2_grad_chain_owner_a.md`。
- 结论：梯度链正常不等价于方案可行，仍归为优化对抗或方法边界。证据：`notes/feature_loss_failure_attribution_minpack.md`、`docs/report_pack/2026-02-26-v22/failure_cases.md`。

## 复现路径（答辩可直接引用）
- 协议与执行：`docs/protocol.yaml`、`docs/execution/2026-02-26-planb.md`。
- 报表与证据快照：`docs/report_pack/2026-02-26-v22/`、`artifacts/report_packs/SHA256SUMS.txt`。
- 打包脚本与可重复生成：`scripts/build_report_pack.py`、`scripts/summarize_scoreboard.py`、`scripts/summarize_planb_anticherrypick.py`、`scripts/pack_evidence.py`。
