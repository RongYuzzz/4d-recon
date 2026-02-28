# protocol_v2 stage-2 trade-off qualitative note（Owner A）

## 对比视频（step599）

- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/baseline_vs_planbfeat_full600_step599.mp4`

## 指标对齐（test@step599）

- `baseline_600`: PSNR `18.9496`, LPIPS `0.4048`, tLPIPS `0.0230`
- `planb_init_600`: PSNR `20.4488`, LPIPS `0.3497`, tLPIPS `0.00720`
- `planb_feat_v2_full600_start300_ramp200_every16`: PSNR `20.5725`, LPIPS `0.3515`, tLPIPS `0.00756`

结论：在 `planb_init_600 -> planb_feat_v2_full600_*` 上出现典型 trade-off：**PSNR 上升**（`+0.1237`）但 **LPIPS/tLPIPS 变差**（`+0.00184/+0.00037`）。

## 画面口径（用于答辩）

- `baseline_600 -> planb_init_600`：整体稳定性与细节都有明显提升（对应 stage-1 的主收益）。
- `planb_init_600 -> planb_feat_v2_full600_*`：高频细节更“硬/锐”，但局部时序更敏感，表现为轻微闪动/漂移感增加。
- `baseline_600 -> planb_feat_v2_full600_*`：相对 baseline 仍是显著整体提升，但并未完全继承 `planb_init_600` 的最佳时序稳定性。

## 代表性失败片段

- 建议片段：`outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`
- 诊断产物：
  - `outputs/report_pack/diagnostics/temporal_diff_curve_planb_vs_planbfeat_test_step599.png`
  - `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`
- 审计锚点（来自 top-k 表）：
  - rank1: `frame_prev=41, frame_cur=42, delta_mean_abs_diff=+0.00034195`
  - rank2: `frame_prev=37, frame_cur=38, delta_mean_abs_diff=+0.00028545`
  - rank3: `frame_prev=39, frame_cur=40, delta_mean_abs_diff=+0.00022669`
- 说明：后续答辩统一引用 top-k 帧对（`frame_prev=X, frame_cur=Y`）而非口语化秒数描述。
