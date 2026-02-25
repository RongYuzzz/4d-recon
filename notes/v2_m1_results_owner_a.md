# Feature-Loss v2 Gate M1 结果（Owner A，200-step）

## 1) 执行命令（GPU0）

```bash
GPU=0 MAX_STEPS=200 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200 \
  bash scripts/run_train_baseline_selfcap.sh

GPU=0 MAX_STEPS=200 TOKEN_LAYER_IDX=17 RESULT_TAG=feature_loss_v2_smoke200 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh

GPU=0 MAX_STEPS=200 TOKEN_LAYER_IDX=17 RESULT_TAG=feature_loss_v2_gated_smoke200 \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```

## 2) test@199 指标

| run | PSNR | LPIPS | tLPIPS | vs baseline_smoke200 |
| --- | ---: | ---: | ---: | --- |
| baseline_smoke200 | 12.6315 | 0.63023 | 0.08774 | baseline |
| feature_loss_v2_smoke200 | 12.5438 | 0.62999 | 0.08326 | ΔPSNR=-0.0877, ΔLPIPS=-0.00025, ΔtLPIPS=-0.00448 |
| feature_loss_v2_gated_smoke200 | 12.5357 | 0.63067 | 0.08337 | ΔPSNR=-0.0958, ΔLPIPS=+0.00044, ΔtLPIPS=-0.00437 |

对应文件：
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_gated_smoke200/stats/test_step0199.json`

## 3) 吞吐与止损线

- baseline_smoke200：73.6s（约 2.717 step/s）
- feature_loss_v2_smoke200：77.0s（约 2.597 step/s）
- feature_loss_v2_gated_smoke200：75.7s（约 2.642 step/s）
- 未触发“吞吐 >2x”止损。

## 4) gated 有效性检查（关键）

`v2_gated` 日志包含：
- `gating=framediff`
- `has_gate_framediff=True`

且未出现：
- `gating='framediff' is not implemented in v1. Falling back to 'none'`

证据日志：
- `/tmp/v2_rerun_feature_loss_v2_gated_smoke200.stdout`

## 5) M1 结论

- 判定：**PASS**（非灾难退化 + 吞吐可控 + gated 生效）
- 决策：进入 Gate M2（两次 full600 上限）。
