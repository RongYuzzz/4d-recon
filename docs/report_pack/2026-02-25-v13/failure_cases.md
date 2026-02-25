# Failure Cases (Midterm, 2026-02-25, Protocol v1)

当前文档用于汇报中的失败机理与证据路径记录，随 evidence 打包。

## Case 1: 短预算 + 稀疏几何导致点云塌缩（gs8@200）
- 现象：`outputs/sweep_selfcap_baseline_gs8/videos/traj_4d_step199.mp4` 中段出现主体消失与稀疏噪点。
- 机制：短预算下 relocation/优化不足，叠加稀疏 triangulation 导致几何退化。
- 证据：`outputs/report_pack/failure_viz/case1_gs8_density_collapse.png`

## Case 2: baseline600 动态边界拖影
- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4` 出现边界雾化重影。
- 机制：快速运动与遮挡切换下，线性时序建模在边界处发生错配。
- 证据：`outputs/report_pack/failure_viz/case2_baseline_motion_smear.png`

## Case 3: ours-weak600 仍有残余拖影
- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/videos/traj_4d_step599.mp4` 仍有残余 smear。
- 机制：weak 注入本质是 photometric reweighting，难以直接修正几何/速度场系统误差。
- 证据：`outputs/report_pack/failure_viz/case3_weak_residual_smear.png`

## Case 4: ours-strong600 无稳定优势
- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600/videos/traj_4d_step599.mp4` 未体现稳定收益。
- 机制：稀疏对应信号受遮挡与噪声影响，early-only corr 约束不足。
- 证据：`outputs/report_pack/failure_viz/case4_strong_no_gain.png`

## Case 5: strong v3 的 trade-off（收益未达成功线）
- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/videos/traj_4d_step599.mp4`
  与 weak/baseline 对比时，tLPIPS 有小幅下降，但 LPIPS 与 PSNR 同时退化。
- 机制：更强的时序约束在当前设定下提升了时间一致性，但牺牲了空间重建质量，形成不可接受 trade-off。
- 判定：按项目 stoploss 口径，strong v3 判定为“未达成功线”，冻结不入主线。
- 参考：`notes/ours_strong_v3_gated_attempt.md`

## Case 6: VGGT cue probe 无收益（weak 注入未改善）
- 现象：`outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600/videos/traj_4d_step599.mp4`
  训练可稳定收敛，但测试指标未优于 `ours_weak_600` / `control_weak_nocue_600`。
- 机制：VGGT cue 虽然非退化（非全黑/全白），但 `temporal_flicker_l1_mean` 偏高，注入后对目标误差抑制不足。
- 判定：当前 VGGT cue 方案不支持开启 `protocol_v2`，继续停留在 probe 结论层。
- 参考：`notes/weak_vggt_probe_selfcap_bar.md`
