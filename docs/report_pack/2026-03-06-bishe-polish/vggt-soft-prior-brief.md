# VGGT Soft-Prior Brief

## Original proposal target

原版开题 `4D-Reconstruction.md` 的前两条主线，分别是：

1. 从 `VGGT` 中挖掘潜在实例语义与动态线索，形成几何一致的伪掩码或弱监督线索；
2. 利用 `VGGT` 的全局注意力/对应关系，向 4DGS 优化闭环中注入时空一致约束。

因此，`VGGT` 这条线真正需要回答的不是“有没有把所有损失都跑成稳定正结果”，而是：我们是否已经把 `VGGT` 变成了一个可解释、可缓存、可注入的 **soft prior** 来源，并且能清楚说明它的证据边界。

## What was actually implemented

当前已经落地的部分主要有三块：

- `cue / pseudo mask`：把 VGGT 线索导出成可落盘的 `pseudo mask`，并给出质量统计与 overlay 可视化；
- `token_proj PCA`：把 feature 本体做 `PCA -> RGB` 映射，展示跨视角 feature 结构；
- `sparse correspondence visualization`：把 token/patch 级 top-k 匹配画出来，说明“对应关系”这件事至少已经有最小可解释闭环。

这些内容已经足以支撑“VGGT 不是一句空口号，而是形成了可审计的 soft-prior 证据包”。但它们与“stage-2 训练已经稳定见效”不是同一层结论。

## Evidence 1: cue / pseudo mask

证据文件：

- `notes/protocol_v2_vggt_cue_viz.md`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/grid_frame000000.jpg`

这部分回答的是：`VGGT` 是否能给出某种与动态/前景相关的弱线索。现有证据表明答案是“能，但较稀疏、有失败边界”。因此它更适合被表述为 frozen `pseudo mask` / weak cue，而不是高质量语义 GT。

## Evidence 2: token_proj PCA

证据文件：

- `notes/protocol_v2_vggt_feature_pca.md`
- `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/viz_pca/grid_pca_frame000000.jpg`

这部分回答的是：`VGGT` feature 本体是否真的包含结构信息，而不是只有一张 overlay。`PCA` 可视化至少说明：多视角 token_proj 特征具备可分解、可对照、可展示的结构模式，能够作为“几何语义线索存在”的直接证据。

## Evidence 3: sparse correspondence visualization

证据文件：

- `notes/protocol_v2_sparse_corr_viz.md`
- `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam02_frame000000_to_000001.jpg`

这部分回答的是：原版开题里“注意力/对应关系”并非完全停留在概念层，而是已经缩成了一个 timeboxed、稀疏化、可可视化的 `sparse correspondence` 版本。它是“可解释示意”和“后续可注入训练信号”的桥梁，但还不是成熟稳定的最终优化器。

## What this proves

这组 soft-prior 证据包可以支撑以下较强但克制的结论：

- `VGGT` 线索提取已经落地为可缓存、可审计、可展示的中间产物；
- 原版开题中的“语义/动态线索提取”这条路线不是空转，已经拿到 `pseudo mask`、feature `PCA` 和 `sparse correspondence` 三种互补证据；
- `VGGT` 在当前项目里最稳妥的定位是 **interpretability evidence + soft prior source**，而不是已被证明能稳定带来全指标收益的主增益模块。

## What it does not prove

这组材料**不能**证明以下说法：

- 不能证明 `stage-2` 已经成为稳定的正收益训练线；
- 不能证明 `VGGT` 约束已经稳定转化为 `PSNR / LPIPS / tLPIPS` 的全面改善；
- 不能把 `interpretability evidence` 直接等同于 `optimization gain evidence`。

与 `docs/report_pack/2026-02-27-v2/scoreboard.md`、`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md` 以及 `notes/protocol_v2_stage2_tradeoff_qual.md` 对齐后的最稳妥口径是：当前 `stage-2` 仍属于 mixed/trade-off 证据，因此 `VGGT` 线的主要价值在于 soft prior / 可解释性闭环，而不是稳定增益闭环。

## Three-level conclusion

- 已完成：VGGT 线索提取、可视化与稀疏对应示意。
- 部分完成：soft prior 注入与 stage-2 训练闭环。
- 尚未闭环：把 VGGT 约束稳定转化为全指标收益。
