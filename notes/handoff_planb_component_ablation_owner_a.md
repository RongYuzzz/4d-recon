# Handoff: Plan-B 组件消融 smoke200（Owner A -> Owner B）

- 日期：2026-02-26
- 计划：`~/docs/plans/2026-02-26-owner-a-planb-component-ablation-smoke200.md`
- 状态：已完成（A71-A75 前置内容完成，待本次文本提交）

## 可直接引用的 RESULT_DIR（3 个变体）

- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_no_drift_smoke200/`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_no_mutual_smoke200/`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ablate_clip_p95_smoke200/`

## 对照目录（便于写作拼表）

- baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window/`
- planb default：`outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/`
- ablation init stats：`outputs/plan_b_ablation/selfcap_bar_8cam60f/*/velocity_stats.json`
- 结论文档：`notes/planb_component_ablation_smoke200_owner_a.md`

## 一句话正文结论

禁用 `mutual NN` 会显著恶化 Plan-B 的时序与感知指标（相对 default：`tLPIPS +0.0135`、`LPIPS +0.0097`、`PSNR -0.0534`），说明该组件对收益是必要的。
