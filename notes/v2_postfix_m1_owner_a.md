# Feature-Loss v2 Post-Fix：Gate M1 记录（Owner A）

## 1) 执行命令（GPU0）

```bash
# baseline smoke200（对照）
GPU=0 MAX_STEPS=200 \
  RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_postfix \
  bash scripts/run_train_baseline_selfcap.sh

# v2 smoke200（post-fix 默认）
GPU=0 MAX_STEPS=200 \
  RESULT_TAG=feature_loss_v2_smoke200_postfix \
  bash scripts/run_train_feature_loss_v2_selfcap.sh

# v2_gated smoke200（framediff）
GPU=0 MAX_STEPS=200 \
  RESULT_TAG=feature_loss_v2_gated_smoke200_postfix \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh

# 最小 lambda sweep（2 点）
GPU=0 MAX_STEPS=200 LAMBDA_VGGT_FEAT=0.005 \
  RESULT_TAG=feature_loss_v2_smoke200_postfix_lam0.005 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh

GPU=0 MAX_STEPS=200 LAMBDA_VGGT_FEAT=0.01 \
  RESULT_TAG=feature_loss_v2_smoke200_postfix_lam0.01 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```

## 2) 产物核验

以下 run 均已生成 `stats/test_step0199.json` 与 `videos/traj_4d_step199.mp4`：
- `baseline_smoke200_postfix`
- `feature_loss_v2_smoke200_postfix`
- `feature_loss_v2_gated_smoke200_postfix`
- `feature_loss_v2_smoke200_postfix_lam0.005`
- `feature_loss_v2_smoke200_postfix_lam0.01`

且 4 条 v2 run 均生成 `stats/throughput.json`。

## 3) 指标汇总（test@199）

baseline（对照）：
- `baseline_smoke200_postfix`: `PSNR=12.6328, LPIPS=0.630614, tLPIPS=0.087738`

对照与 sweep：
- `feature_loss_v2_smoke200_postfix`
  - `PSNR=12.6161, LPIPS=0.630005, tLPIPS=0.085902`
  - vs baseline: `ΔPSNR=-0.0167, ΔLPIPS=-0.000610, ΔtLPIPS=-0.001835`
  - `iter_per_sec=15.9980`
- `feature_loss_v2_gated_smoke200_postfix`
  - `PSNR=12.6150, LPIPS=0.630412, tLPIPS=0.086388`
  - vs baseline: `ΔPSNR=-0.0178, ΔLPIPS=-0.000202, ΔtLPIPS=-0.001350`
  - `iter_per_sec=14.1352`
- `feature_loss_v2_smoke200_postfix_lam0.005`
  - `PSNR=12.6286, LPIPS=0.630230, tLPIPS=0.086826`
  - vs baseline: `ΔPSNR=-0.0042, ΔLPIPS=-0.000384, ΔtLPIPS=-0.000911`
  - `iter_per_sec=14.1035`
- `feature_loss_v2_smoke200_postfix_lam0.01`
  - `PSNR=12.6213, LPIPS=0.630485, tLPIPS=0.086305`
  - vs baseline: `ΔPSNR=-0.0115, ΔLPIPS=-0.000130, ΔtLPIPS=-0.001433`
  - `iter_per_sec=15.2922`

## 4) gated 生效性检查

`/tmp/v2_postfix_feature_loss_v2_gated_smoke200.stdout` 中出现：
- `gating=framediff`
- `has_gate_framediff=True`

且未出现：
- `gating='framediff' is not implemented in v1. Falling back to 'none'`

## 5) M1 判定（按计划阈值）

阈值：
- `ΔPSNR >= -0.5dB`
- `ΔtLPIPS <= +0.01`
- 吞吐不低于 baseline 的 0.5 倍（粗判）

结果：
- 所有 v2/v2_gated/sweep 点均满足上述阈值；
- wall-clock 时间：baseline 73.2s；v2 75.7s；v2_gated 77.6s；未触发吞吐止损。

**结论：M1 PASS，可进入 Task 3（选择性 full600）。**
