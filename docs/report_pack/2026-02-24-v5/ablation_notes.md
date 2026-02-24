# Ablation Notes (Midterm, 2026-02-24, Protocol v1)

本文件是“汇报用文字说明”的一部分，随 `scripts/pack_evidence.py` 打包（`outputs/report_pack/`）。

## Protocol
- Frozen protocol：`docs/protocol.yaml`（v1）
- 数据：`data/selfcap_bar_8cam60f`（SelfCap bar，8 cams × 60 frames）
- split：train `02-07` / val `08` / test `09`
- 预算：`MAX_STEPS=600`（step=599 写入 `*_step0599.json`）
- test 上启用 `tLPIPS`（`eval_sample_every_test=1`）

## Current Coverage (Protocol v1 / SelfCap bar 8cam60f)

（以下均为 step599 的均值指标；val/test 分开列出。）

1. Baseline（FreeTimeGsVanilla）
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600`
- val：PSNR 18.4650 / SSIM 0.6432 / LPIPS 0.4217
- test：PSNR 18.9496 / SSIM 0.6653 / LPIPS 0.4048 / tLPIPS 0.0230

2. Ours-Weak（cue mining + mask-weighted photometric, tuned defaults）
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600`
- cue：`outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz`（backend=diff）
- params：`PSEUDO_MASK_WEIGHT=0.3`，`PSEUDO_MASK_END_STEP=200`
- val：PSNR 18.5020 / SSIM 0.6442 / LPIPS 0.4206
- test：PSNR 19.0194 / SSIM 0.6661 / LPIPS 0.4037 / tLPIPS 0.0231

3. Control（Weak codepath but no cue）
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600`
- cue：`backend=zeros`（常量 mask，作为 “weak 注入路径” 的 control）
- val：PSNR 18.5926 / SSIM 0.6439 / LPIPS 0.4189
- test：PSNR 19.1099 / SSIM 0.6674 / LPIPS 0.4033 / tLPIPS 0.0236
- 备注：理论上该 control 的 loss 与 baseline 等价（mask=0 => w=1），但 GPU 训练存在微小非确定性，指标会有轻微波动；该 run 的意义是验证“weak 代码路径本身不应引入灾难性回归”。

4. Ours-Strong（temporal correspondences + corr loss）
- dir：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600`
- corr：`outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`
- params：`LAMBDA_CORR=0.01`，`TEMPORAL_CORR_END_STEP=200`，`TEMPORAL_CORR_MAX_PAIRS=200`
- val：PSNR 18.4990 / SSIM 0.6445 / LPIPS 0.4236
- test：PSNR 19.0236 / SSIM 0.6660 / LPIPS 0.4094 / tLPIPS 0.0233

强融合审计说明（命令/稳定性/结论）见：
- `notes/ours_strong_attempt_selfcap_bar.md`
- `notes/ours_strong_sweep_selfcap_bar.md`

## Same-Budget Readout (test@step599, cam09)

| Method | PSNR | SSIM | LPIPS | tLPIPS |
| --- | --- | --- | --- | --- |
| baseline | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| ours-weak (w=0.3,end=200) | 19.0194 | 0.6661 | 0.4037 | 0.0231 |
| control (no cue) | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| ours-strong (lam=0.01) | 19.0236 | 0.6660 | 0.4094 | 0.0233 |

阶段性结论（midterm 口径）：
- weak：在 tuned 配置下不明显劣于 baseline（略有改善或持平）。
- strong：本轮 attempt 可复现且可审计，但在同预算下未呈现稳定优势（stoploss）。

## Commands Used (Protocol v1)

```bash
cd /root/projects/4d-recon

# Baseline
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600 \
bash scripts/run_train_baseline_selfcap.sh

# Ours-Weak (tuned defaults)
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600 \
bash scripts/run_train_ours_weak_selfcap.sh

# Control: weak-no-cue
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600 \
bash scripts/run_train_control_weak_nocue_selfcap.sh

# Ours-Strong
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600 \
bash scripts/run_train_ours_strong_selfcap.sh
```

