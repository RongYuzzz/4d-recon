# Bishe Final Polish Pack

## What is the mainline result?

主线硬结果仍然是 `Plan-B`：也就是基于线性速度初始化/动静表征底座的 stage-1 收益线。与 `baseline_600` 相比，`Plan-B` 在 `SelfCap` 主证据链上给出了最稳定、最可审计的提升，这也是当前毕设最应该首先强调的主结果。对应入口：

- `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- `docs/report_pack/2026-02-27-v2/README.md`

## What is the innovation story?

当前最稳妥的创新叙事不是“stage-2 已经全面跑赢”，而是两条已经形成闭环的补充贡献：

1. `VGGT` 作为 frozen `soft prior` 的可解释证据链：包括 `pseudo mask`、feature `PCA`、token 级 `sparse correspondence`；
2. `dynamic/static` 导出与 removal-style demo：把“可编辑性”从抽象目标落成可视化证据。

这两条 together，回答的是：这个项目不只是复现 baseline，而是在主线 `Plan-B` 之外，进一步把“几何语义 soft prior + dynamic/static 可编辑证据”做成了论文/答辩可用的完整包。

## What is the strongest demo?

最强 demo 不是新的训练曲线，而是 `dynamic/static` 编辑演示：

- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/qualitative_local/bishe_edit_demo_frames/`

它最适合支撑“动静解耦 + removal-style 可编辑性”的现场说明，因为 reviewer 不需要先看复杂指标，就能直观看到 `dynamic/static` 两层已经可导出、可对照、可解释。

## What is the honest limitation?

最需要诚实说明的限制有两条：

- `stage-2` 目前仍是 `mixed/trade-off`，没有成为稳定正收益主线；
- 当前编辑演示是 filtering-based evidence，不是完整 object editing / inpainting system。

因此，最终交付应该坚持“主线结果靠 Plan-B，创新性与学术完整性靠 soft prior + dynamic/static 证据包”这一口径，而不是把 mixed/trade-off 的探索线包装成稳定突破。

## Which 3 files should a busy reviewer open first?

只看三份文件时，建议按下面顺序打开：

1. `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
2. `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
3. `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`

## Three files first

- `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
- `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`

## Reviewer shortcut

如果 reviewer 只想快速判断“这份毕设是不是不止复现”，看法可以收敛为三句话：

- 主结果：`Plan-B` 是硬结果；
- 创新点：`soft prior` + `dynamic/static` 两条补充线已经落地为证据包；
- 边界：`stage-2` 仍是 mixed/trade-off，因此本包坚持诚实收口，不做过度外推。
