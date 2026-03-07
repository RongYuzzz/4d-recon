# Original Proposal Alignment

## Alignment table

| Original route item | Current status | Evidence |
|---|---|---|
| 开源 4DGS 适配 + 线性运动/动静解耦底座 | Done | `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`; `notes/protocol_v2_static_dynamic_tau.md`; `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4` |
| VGGT latent cue mining / 几何语义 weak cue 提取 | Done | `notes/protocol_v2_vggt_cue_viz.md`; `notes/protocol_v2_vggt_feature_pca.md`; `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json` |
| 注意力/对应关系引导的时空一致约束 | Exploratory | `notes/protocol_v2_sparse_corr_viz.md`; `docs/report_pack/2026-02-27-v2/scoreboard.md`; `notes/protocol_v2_stage2_tradeoff_qual.md` |
| VGGT soft-prior 注入后的 stage-2 训练闭环 | Partial | `docs/report_pack/2026-02-27-v2/scoreboard.md`; `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`; `notes/protocol_v2_stage2_tradeoff_qual.md` |
| 动静解耦 + removal-style 物体移除定性演示 | Partial | `notes/protocol_v2_static_dynamic_tau.md`; `notes/openproposal_phase5_edit_demo.md`; `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4` |
| “多数据集 + 全指标稳定优于外部先验方法”这类强主张 | Superseded by v2 narrowing | `4D-Reconstruction.md`; `4D-Reconstruction-v2.md`; `docs/decisions/2026-02-27-dual-stage-academic-completeness.md` |
| oracle backgroundness weak-fusion 补充诊断线 | Exploratory | `notes/2026-03-06-thuman4-oracle-weak-decision.md` |

## Bottom-line self-evaluation

从原版开题真正落地的部分看，项目已经完成了三类硬工作：一是把 4DGS/FreeTimeGS 物理底座适配到当前数据协议，并做出 `Plan-B` 这一条主增益线；二是把 `VGGT` 从抽象概念落成了可缓存、可视化、可注入的 soft prior 证据包；三是做出了 `dynamic/static` 导出与 removal-style 演示，把“可编辑性”从口头描述变成了可播放的定性材料。

被 `v2` 主动收窄的部分主要有两类：第一，原版里最强的“多数据集 + 全指标稳定优于”的性能目标，没有在当前周期内完成，因此已被 `4D-Reconstruction-v2.md` 明确缩成“以 SelfCap 主证据链 + tLPIPS + 可解释/可编辑补闭环”为核心；第二，原版里的“注意力引导对比损失”没有发展成稳定正结果，目前只能诚实归为 `Exploratory` / `Partial`，并以 mixed/trade-off 口径收口。

在这个前提下，当前项目仍然可以较客观地支撑“工作量饱满 + 有一点创新性”：工作量来自完整的底座复现与改造、协议化评测、soft-prior 可解释材料、stage-2 训练尝试、额外 oracle-weak 负线诊断与最终收口；创新性则主要体现在“无需外部 2D 强监督前置，把 VGGT 作为 frozen soft prior 嵌入 4DGS，并同时提供 dynamic/static 可编辑性证据”这条相对完整、且与原版开题同方向的技术叙事上。它不是“所有目标都完全证实”的版本，但已经是一个边界清楚、证据成包、可自洽答辩的版本。
