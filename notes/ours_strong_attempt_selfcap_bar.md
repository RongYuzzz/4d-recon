# Ours-Strong Attempt Audit (SelfCap Bar 8cam60f)

日期：2026-02-24  
分支：`owner-b-20260224-strong-v2`  
目标：在协议预算内完成 strong 尝试（v1 + v2），并给出可复现、可审计、可决策的结论。

## 1) V2 可复现命令（Temporal Consistency）

### 1.1 60-step smoke

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-strong-v2
GPU=1 MAX_STEPS=60 \
DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f \
RESULT_DIR=/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_smoke60 \
TEMPORAL_CORR_NPZ=/root/projects/4d-recon/outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/temporal_corr.npz \
LAMBDA_CORR=0.01 TEMPORAL_CORR_END_STEP=60 TEMPORAL_CORR_MAX_PAIRS=200 \
TEMPORAL_CORR_LOSS_MODE=pred_pred \
PSEUDO_MASK_NPZ=/root/projects/4d-recon/outputs/cue_mining/selfcap_bar_8cam60f_diff_midterm_600/pseudo_masks.npz \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=60 \
bash scripts/run_train_ours_strong_selfcap.sh
```

### 1.2 200-step sweep（3 组）

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-strong-v2
for lam in 0.005 0.01 0.02; do
  GPU=1 MAX_STEPS=200 \
  DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f \
  RESULT_DIR=/root/projects/4d-recon/outputs/sweeps/selfcap_bar_strong_v2_lam${lam}_end200_pairs200_s200 \
  TEMPORAL_CORR_NPZ=/root/projects/4d-recon/outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/temporal_corr.npz \
  LAMBDA_CORR=$lam TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
  TEMPORAL_CORR_LOSS_MODE=pred_pred \
  PSEUDO_MASK_NPZ=/root/projects/4d-recon/outputs/cue_mining/selfcap_bar_8cam60f_diff_midterm_600/pseudo_masks.npz \
  PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
  bash scripts/run_train_ours_strong_selfcap.sh
done
```

### 1.3 600-step full run（按 sweep 最稳组）

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-strong-v2
GPU=1 MAX_STEPS=600 \
DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f \
RESULT_DIR=/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_600 \
TEMPORAL_CORR_NPZ=/root/projects/4d-recon/outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/temporal_corr.npz \
LAMBDA_CORR=0.005 TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
TEMPORAL_CORR_LOSS_MODE=pred_pred \
PSEUDO_MASK_NPZ=/root/projects/4d-recon/outputs/cue_mining/selfcap_bar_8cam60f_diff_midterm_600/pseudo_masks.npz \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

## 2) 对应数据与证据路径

- 对应文件（v2）：`outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/temporal_corr.npz`
- 对应可视化（v2）：`outputs/correspondences/selfcap_bar_8cam60f_klt_fb_v2/viz/*`
- 生成说明：`notes/selfcap_temporal_corr_klt.md`
- full run 日志：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_600/run.log`
- smoke 日志：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_smoke60/run.log`

关键日志证据（full run）：
- `[StrongFusion] Loaded temporal correspondences ... mode=pred_pred`
- `[StrongFusion] corr_mode=pred_pred corr_pairs=200 ...`
- `[Eval:val] Step 599`
- `[Eval:test] Step 599`
- `[Training] Complete!`
- `[Ours-Strong] Done: .../ours_strong_v2_600`

## 3) 稳定性检查

- `NaN`：未见。
- strong 自动禁用：未见。
- `corr_pairs`：训练期日志观测到 `corr_pairs=200`（非 0）。
- full600 关键产物齐备：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_600/stats/val_step0599.json`
  - `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_600/stats/test_step0599.json`
  - `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_600/videos/traj_4d_step599.mp4`
- 配置核验：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v2_600/cfg.yml` 包含 `temporal_corr_loss_mode: pred_pred`。

## 4) 指标汇总（同预算对比）

数据来源：`outputs/report_pack/metrics.csv`（已刷新，33 行）。

600-step（step=599）：

| Method | split | PSNR | SSIM | LPIPS | tLPIPS |
|---|---|---:|---:|---:|---:|
| baseline_600 | val | 18.4650 | 0.6432 | 0.4217 | - |
| baseline_600 | test | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| ours_weak_600 | val | 18.5020 | 0.6442 | 0.4206 | - |
| ours_weak_600 | test | 19.0194 | 0.6661 | 0.4037 | 0.0231 |
| ours_strong_600 (v1) | val | 18.4990 | 0.6445 | 0.4236 | - |
| ours_strong_600 (v1) | test | 19.0236 | 0.6660 | 0.4094 | 0.0233 |
| ours_strong_v2_600 | val | 18.3811 | 0.6413 | 0.4225 | - |
| ours_strong_v2_600 | test | 18.8095 | 0.6629 | 0.4080 | 0.0247 |

v2 sweep200（step=199）：

| Run | split | PSNR | SSIM | LPIPS | tLPIPS |
|---|---|---:|---:|---:|---:|
| lam=0.005 | val | 13.3403 | 0.2974 | 0.6032 | - |
| lam=0.005 | test | 12.6223 | 0.3064 | 0.6298 | 0.0868 |
| lam=0.01 | val | 13.3249 | 0.2972 | 0.6029 | - |
| lam=0.01 | test | 12.6092 | 0.3063 | 0.6298 | 0.0856 |
| lam=0.02 | val | 13.3108 | 0.2970 | 0.6028 | - |
| lam=0.02 | test | 12.5943 | 0.3065 | 0.6293 | 0.0859 |

## 5) 结论（Stoploss）

结论：**strong v2 在当前配置下不建议继续投入，执行 stoploss。**

依据：
- 与 v1/weak/baseline 同预算对比，`ours_strong_v2_600` 在 val/test 上均无提升，且 test 明显回落。
- 虽然机制更合理（`pred_pred` + KLT FB weight），并且训练稳定可复现，但收益不足以覆盖工程与算力成本。

主要阻塞点：
1. 对应噪声仍然存在，`pred_pred` 约束在早期容易放大偏差。
2. 当前 loss 形态对主重建目标贡献偏弱，未形成稳定增益。
3. 额外 second render 带来开销，但未兑换为质量提升。

建议：
1. 主线继续以 weak 融合推进中期交付。
2. strong 暂存为后备方向，仅在改进对应质量（更长轨迹/多帧一致性/特征空间一致性/attention 过滤）后再做小预算验证。
