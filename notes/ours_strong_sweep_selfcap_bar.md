# Ours-Strong Sweep (SelfCap Bar 8cam60f, 200-step)

日期：2026-02-24  
执行分支：`owner-b-20260224-strong-audit`  
GPU：`GPU=1`  
数据：`/root/projects/4d-recon/data/selfcap_bar_8cam60f`  
对应文件：`/root/projects/4d-recon/outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`

## Sweep 设置

- 固定参数：
  - `MAX_STEPS=200`
  - `TEMPORAL_CORR_END_STEP=200`
  - `TEMPORAL_CORR_MAX_PAIRS=200`
  - `PSEUDO_MASK_WEIGHT=0.2`
  - `PSEUDO_MASK_END_STEP=200`
  - `PSEUDO_MASK_NPZ=/root/projects/4d-recon/outputs/cue_mining/selfcap_bar_8cam60f_diff_midterm_600/pseudo_masks.npz`
- 变量参数：`LAMBDA_CORR in {0.01, 0.02, 0.05}`

## 结果摘要

| lambda | run_dir | val@199 PSNR/SSIM/LPIPS | test@199 PSNR/SSIM/LPIPS/tLPIPS | total time |
|---|---|---|---|---|
| 0.01 | `outputs/sweeps/selfcap_bar_strong_lam0.01_end200_pairs200_s200` | 13.3216 / 0.2974 / 0.6046 | 12.6147 / 0.3069 / 0.6309 / 0.0874 | 90.5s |
| 0.02 | `outputs/sweeps/selfcap_bar_strong_lam0.02_end200_pairs200_s200` | 13.3152 / 0.2973 / 0.6045 | 12.6086 / 0.3069 / 0.6311 / 0.0875 | 91.2s |
| 0.05 | `outputs/sweeps/selfcap_bar_strong_lam0.05_end200_pairs200_s200` | 13.3041 / 0.2968 / 0.6056 | 12.5903 / 0.3059 / 0.6314 / 0.0874 | 90.4s |

对应产物（每组）：
- `videos/traj_4d_step199.mp4`
- `stats/val_step0199.json`
- `stats/test_step0199.json`
- `run.log`

## 稳定性观察

- 三组均成功完成 200-step，未出现 `NaN`。
- 三组日志均出现：`[StrongFusion] Loaded temporal correspondences...`。
- 三组日志均未出现：`Strong fusion disabled`。
- `corr_pairs` 标量未在当前日志口径中逐步打印，无法直接从日志做时间序列核验。
- 速度粗看稳定：首步约 3.1~3.2s，整体 `~90s/200step`（均值约 0.45s/step）。

## 定性观测（基于轨迹视频）

- 三组都可见到动态区域重建可用，未出现明显训练崩溃或大面积几何炸裂。
- `lambda=0.01` 在当前 200-step 下指标最稳，且 test PSNR/LPIPS 略优于另两组。
- 因 0.01/0.02 差距很小，后续 full run 采用 `lambda=0.01` 作为保守候选。
