# protocol_v2 spatial metrics diagnostics（test_step599）

## Inputs

- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders`

## Method

- 从 `test_step599_*.png` 读取 GT|Pred 横向拼接图，左半切 GT、右半切 Pred。
- 逐帧计算 `MAE/MSE/PSNR`，导出两条 run 的 per-frame CSV。
- 基于两条 CSV 生成 `planbfeat - planb` 的 delta CSV、曲线图、top-k 表。
- 本次环境缺少 `torchmetrics`，未生成 LPIPS 列（仅 CPU 指标交付）。

## Key Findings

- `PSNR`（via `MSE`）在所有帧上均提升（`delta_psnr > 0` / `delta_mse < 0`）。
- `MAE` 存在局部劣化：`delta_mae > 0` 的帧为 `15/60`，主要集中在 `52-59`（另有少量早段帧如 `0-3`）。
- `41/42` 邻域的 `delta_mae < 0`（MAE 改善），与 temporal diff / tLPIPS 的主峰（`41->42`）不完全对齐；该现象提示“像素域误差”与“感知/时序指标”可能关注不同失败模式。
- `spatial_metrics_topk_*.md` 的排序口径为 `delta_mae`（不是按 `PSNR` 排序）。

## Artifacts (repo-relative paths)

- `outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv`
- `outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv`
- `outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv`
- `outputs/report_pack/diagnostics/spatial_metrics_curve_planb_vs_planbfeat_test_step599.png`
- `outputs/report_pack/diagnostics/spatial_metrics_topk_planbfeat_minus_planb_test_step599.md`
