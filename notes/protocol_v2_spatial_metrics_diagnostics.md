# protocol_v2 spatial metrics diagnostics（test_step599）

## Inputs

- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/renders`
- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/renders`

## Method

- 从 `test_step599_*.png` 读取 GT|Pred 横向拼接图，左半切 GT、右半切 Pred。
- 逐帧计算 `MAE/MSE/PSNR`，导出两条 run 的 per-frame CSV。
- 基于两条 CSV 生成 `planbfeat - planb` 的 delta CSV、曲线图、top-k 表。
- 本次环境缺少 `torchmetrics`，未生成 LPIPS 列（仅 CPU 指标交付）。

## Key Findings

- top-k（按 `delta_mae` 降序）最差帧主要集中在 `59,58,57,56,55,54,53,52,51`（另有 `0`）。
- 最差 top-k 未直接命中 `41/42`；在 top-20 中出现邻近帧 `44/45`，说明劣化峰值更偏后段（约 `44-59`）。

## Artifacts (absolute paths)

- `/root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics/spatial_metrics_planb_init_600_test_step599.csv`
- `/root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics/spatial_metrics_planb_feat_v2_full600_test_step599.csv`
- `/root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv`
- `/root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics/spatial_metrics_curve_planb_vs_planbfeat_test_step599.png`
- `/root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics/spatial_metrics_topk_planbfeat_minus_planb_test_step599.md`
