# Docs Index

当前以“能跑、可复现、可答辩”为第一优先级，文档入口建议按以下顺序看：

1. `README.md`
   - 主入口命令、Gate-0/Gate-1 说明、SelfCap canonical adapter。
   - 总执行计划：`docs/execution/2026-02-12-4d-reconstruction-execution.md`
2. `docs/protocol.yaml`
   - 唯一评测/训练协议真源（冻结，改动必须版本升级）。
3. `notes/demo-runbook.md`
   - 现场演示命令（尽量只依赖主阵地 `/root/projects/4d-recon`）。
4. `notes/data-manifest.md`
   - 当前数据路径与历史产物清单（含可选清理项）。
5. `notes/decision-log.md`
   - 关键决策与验证记录（为什么这样做、什么时候定版）。
6. `notes/t0-gate-decision.md` + `scripts/t0_grad_check.md`
   - T0 审计结论与梯度检查口径。
7. `docs/report_pack/`
   - 汇报材料快照（文本版，便于长期保存）。
8. `docs/writing/planb_paper_outline.md`
   - 写作骨架与证据路径索引（论文/答辩可直接复用）。
9. `artifacts/report_packs/`（本地）
   - 离线证据包 tarball（不进 git，建议另行备份）。

`docs/plans/` 下是执行计划/分工记录：大多数已标注“存档”，用于追溯过程；`Next` 类计划则用于后续推进。
