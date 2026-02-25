# Feature-Loss v2 Gate M2 结果（Owner A，full600）

## 1) 执行命令（GPU0；两次 full600）

```bash
GPU=0 MAX_STEPS=600 TOKEN_LAYER_IDX=17 RESULT_TAG=feature_loss_v2_600 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh

GPU=0 MAX_STEPS=600 TOKEN_LAYER_IDX=17 RESULT_TAG=feature_loss_v2_gated_600 \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```

## 2) 产物核验

两条 run 均存在：
- `stats/test_step0599.json`
- `videos/traj_4d_step599.mp4`
- `stats/throughput.json`

路径：
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_600/`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_gated_600/`

## 3) test@599 指标对比

参考（已有 canonical）：
- baseline_600: `PSNR=18.9496, LPIPS=0.4048, tLPIPS=0.0230`
- control_weak_nocue_600: `PSNR=19.1099, LPIPS=0.4033, tLPIPS=0.0236`

本轮：
- feature_loss_v2_600: `PSNR=15.9437, LPIPS=0.4996, tLPIPS=0.0462`
- feature_loss_v2_gated_600: `PSNR=15.1714, LPIPS=0.5140, tLPIPS=0.0507`

相对 baseline_600：
- v2_600: `ΔPSNR=-3.0059, ΔLPIPS=+0.0948, ΔtLPIPS=+0.0232`
- v2_gated_600: `ΔPSNR=-3.7782, ΔLPIPS=+0.1092, ΔtLPIPS=+0.0278`

相对 control_weak_nocue_600：
- v2_600: `ΔPSNR=-3.1661, ΔLPIPS=+0.0963, ΔtLPIPS=+0.0226`
- v2_gated_600: `ΔPSNR=-3.9385, ΔLPIPS=+0.1107, ΔtLPIPS=+0.0271`

## 4) 吞吐与 gated 运行有效性

- feature_loss_v2_600：总时长 113.1s；`throughput.iter_per_sec=15.1493`
- feature_loss_v2_gated_600：总时长 113.0s；`throughput.iter_per_sec=14.0625`
- 吞吐未触发 >2x 止损。

gated 运行有效性（非 v1 fallback）：
- 日志出现 `gating=framediff`、`has_gate_framediff=True`
- 未出现 `Falling back to 'none'`
- 证据：`/tmp/v2_rerun_feature_loss_v2_gated_600.stdout`

## 5) M2 成功线判定

按 `docs/execution/2026-02-26-feature-loss-v2.md`：
- `tLPIPS` 下降 ≥10%：**不满足**
- 或 `LPIPS` 下降 ≥0.01：**不满足**
- 或 `PSNR` +0.2 dB：**不满足**

结论：**M2 FAIL（两次 full600 均无正向趋势且出现显著退化）**。

执行决策：**触发 stoploss，停止继续追加 full600，转入失败归因/Plan‑B 评估**。

## 6) 版本说明

- 本轮 full600 运行基于提交 `2948fa0` 的脚本默认（日志显示 `lambda=0.05, ramp=200`）。
- 完成后远端 `origin/main` 前进到 `a859078`（主要调整 `run_train_feature_loss_v2_selfcap.sh` 的保守默认参数）。
