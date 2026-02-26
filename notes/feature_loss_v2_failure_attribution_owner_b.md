# Feature-Loss v2 失败归因（Owner B, No-GPU, 2026-02-26）

## 结论摘要

- 在当前可用产物中，`feature_loss_v2_smoke200` / `feature_loss_v2_gated_smoke200` 相对 `baseline_600` 仍显著退化（PSNR/SSIM 下降，LPIPS/tLPIPS 上升）。
- 曲线层面更接近“优化对抗/方法边界”而非“单一显性工程 bug”：`loss/total` 降幅有限，`metrics/psnr` 基本不升，且 `loss_weighted/feat` 后期趋近 0 时画质仍未恢复。
- 执行策略：继续冻结 feature-loss full600，不再追加算力；保留最小归因链用于答辩 negative result。

## 数据范围与说明

- 基线 run：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600`
- v2 失败 run（本次可用）：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200`
- 说明：主仓当前未发现 `feature_loss_v2_postfix_600` 的 TB 目录，因此按“最新可用 v2 失败 run”使用 smoke200 版本。

## 可复现命令（No-GPU）

```bash
cd /root/projects/4d-recon
OUT=outputs/diagnostics
mkdir -p "$OUT"

TAGS='loss/total,loss/l1_raw,loss/feat_raw,loss_weighted/l1,loss_weighted/feat,metrics/psnr,val/psnr,val/lpips,val/tlpips,test/psnr,test/lpips,test/tlpips,gaussians/count'

python3 scripts/export_tb_scalars.py \
  --run_dir /root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600 \
  --out_dir /root/autodl-tmp/projects/4d-recon/outputs/diagnostics \
  --tags "$TAGS" \
  --plot_png

python3 scripts/export_tb_scalars.py \
  --run_dir /root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200 \
  --out_dir /root/autodl-tmp/projects/4d-recon/outputs/diagnostics \
  --tags "$TAGS" \
  --plot_png
```

产物（不入库）：
- `outputs/diagnostics/baseline_600_tb_scalars.csv`
- `outputs/diagnostics/feature_loss_v2_smoke200_tb_scalars.csv`
- `outputs/diagnostics/*_loss_curves.png`

## 曲线观察（基于导出 CSV）

1. `baseline_600`
- `loss/total`: 0.2397 -> 0.1141（显著下降）
- `metrics/psnr`: 13.1010 -> 20.1780（稳定上升）
- `gaussians/count`: 92749 -> 92749（本段无 densify 数量变化）

2. `feature_loss_v2_smoke200`
- `loss/total`: 0.2441 -> 0.2308（下降幅度很小）
- `metrics/psnr`: 13.1010 -> 13.0836（基本停滞）
- `loss/feat_raw`: 0.2180 -> 0.0000（后期趋近 0）
- `loss/l1_raw`: 0.1158 -> 0.1177（未随训练改善）
- `gaussians/count`: 92749 -> 92749（数量稳定，非 densify 引起的波动）

3. 终点评测对照（test）
- `baseline_600@599`: PSNR 18.9496 / SSIM 0.6653 / LPIPS 0.4048 / tLPIPS 0.0230
- `feature_loss_v2_smoke200@199`: PSNR 12.5040 / SSIM 0.2924 / LPIPS 0.6255 / tLPIPS 0.0807

## 已排除项（工程链路）

- `token_proj` 对齐修复与合同测试已存在并通过：`scripts/tests/test_token_proj_resize_alignment.py`。
- cache 合同测试已存在并通过：`scripts/tests/test_vggt_cache_contract.py`。
- 吞吐链路可审计（`stats/throughput.json` 已落盘）；历史记录见 `notes/v2_m2_results_owner_a.md`（未触发 >2x 止损）。

## 仍未知项 / 方法边界

- smoke200 与 full600 的曲线形态是否一致（当前缺少可用 v2 full600 TB）。
- gating 命中区域与 patch 采样分布是否对动态区域真正有效（需要热图统计补充）。
- 在 feature loss 后期弱化时，photometric 分支为何仍未回收质量（可能为早期优化路径依赖）。

## 下一步（不新增 full600）

1. 继续保留 Plan-B 主线，feature-loss 仅保留 No-GPU 归因材料。  
2. 若后续补到 v2 full600 TB，仅追加同口径曲线对照，不新增训练预算。  
3. 在答辩文本中明确：negative result 已排除关键实现风险，结论定位为方法边界/优化对抗。
