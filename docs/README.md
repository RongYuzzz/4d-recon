# Docs Index

当前以“能跑、可复现、可答辩”为第一优先级，文档入口建议按以下顺序看：

1. `README.md`
   - 主入口命令、Gate-0/Gate-1 说明、SelfCap canonical adapter。
   - 总执行计划：`docs/execution/2026-02-12-4d-reconstruction-execution.md`
2. `docs/protocol.yaml`
   - 唯一评测/训练协议真源（冻结，改动必须版本升级）。
3. `docs/decisions/2026-02-26-planb-v26-freeze.md`
   - v26 冻结决议：Plan-B only、feature-loss v2 No-Go、Plan-B+weak No-Go、新增 full600 `N=0`。
4. `notes/demo-runbook.md`
   - 现场演示命令（尽量只依赖主阵地 `/root/projects/4d-recon`）。
5. `notes/data-manifest.md`
   - 当前数据路径与历史产物清单（含可选清理项）。
6. `notes/decision-log.md`
   - 关键决策与验证记录（为什么这样做、什么时候定版）。
7. `notes/t0-gate-decision.md` + `scripts/t0_grad_check.md`
   - T0 审计结论与梯度检查口径。
8. `docs/report_pack/`
   - 汇报材料快照（文本版，便于长期保存）。
9. `docs/reviews/2026-02-26/meeting-index-v26.md` + `docs/reviews/2026-02-26/meeting-handout-v26.md` + `docs/reviews/2026-02-26/meeting-checklist-v26.md`
   - v26 会议入口总索引、单文件 handout 与 2 分钟会前 checklist（会前优先阅读）。
10. `docs/writing/planb_paper_outline.md`
   - 写作骨架与证据路径索引（论文/答辩可直接复用）。
11. `docs/writing/planb_onepager_v26.md` + `docs/writing/planb_talk_outline_v26.md` + `docs/writing/planb_qa_cards_v26.md`
   - v26 冻结期会议写作三件套（一页纸/讲稿大纲/Q&A）。
12. `artifacts/report_packs/`（本地）
   - 离线证据包 tarball（不进 git，建议另行备份）。

`docs/plans/` 下是执行计划/分工记录：大多数已标注“存档”，用于追溯过程；`Next` 类计划则用于后续推进。
