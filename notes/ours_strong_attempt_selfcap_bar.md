# Ours-Strong Attempt Audit (SelfCap Bar 8cam60f)

日期：2026-02-24  
分支：`owner-b-20260224-strong-audit`  
目标：在协议预算内完成 strong 融合尝试，并给出可复现、可审计结论。

## 1) 可复现命令

### 1.1 60-step smoke

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-strong-audit
GPU=1 MAX_STEPS=60 \
DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f \
RESULT_DIR=/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_smoke60 \
TEMPORAL_CORR_NPZ=/root/projects/4d-recon/outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
LAMBDA_CORR=0.05 TEMPORAL_CORR_END_STEP=60 TEMPORAL_CORR_MAX_PAIRS=200 \
PSEUDO_MASK_NPZ=/root/projects/4d-recon/outputs/cue_mining/selfcap_bar_8cam60f_diff_midterm_600/pseudo_masks.npz \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=60 \
bash scripts/run_train_ours_strong_selfcap.sh
```

### 1.2 200-step sweep（3 组）

见：`notes/ours_strong_sweep_selfcap_bar.md`

### 1.3 600-step full run（最终候选）

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-strong-audit
GPU=1 MAX_STEPS=600 \
DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f \
RESULT_DIR=/root/projects/4d-recon/outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_600 \
TEMPORAL_CORR_NPZ=/root/projects/4d-recon/outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz \
LAMBDA_CORR=0.01 TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
PSEUDO_MASK_NPZ=/root/projects/4d-recon/outputs/cue_mining/selfcap_bar_8cam60f_diff_midterm_600/pseudo_masks.npz \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_strong_selfcap.sh |& tee /root/projects/4d-recon/outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_600/run.log
```

说明：
- 计划标准路径 `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600` 已建立软链接，指向 gate1 实际目录，便于协议路径与 gate 统计同时满足。

## 2) Temporal Correspondence 来源与生成方式

- 使用文件：`outputs/correspondences/selfcap_bar_8cam60f_klt/temporal_corr.npz`
- 生成方法与命令：`notes/selfcap_temporal_corr_klt.md`
- 该文件在训练日志中被显式加载：
  - `outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_600/run.log`
  - 日志关键字：`[StrongFusion] Loaded temporal correspondences`

## 3) Matching 可视化证据路径

- 目录：`outputs/correspondences/selfcap_bar_8cam60f_klt/viz`
- 示例截图：
  - `outputs/correspondences/selfcap_bar_8cam60f_klt/viz/frame000000_to_000001_cam02.jpg`
  - `outputs/correspondences/selfcap_bar_8cam60f_klt/viz/frame000000_to_000001_cam09.jpg`

## 4) 训练稳定性与运行口径

- `NaN`：未见（sweep/full 日志均未匹配 `NaN`）。
- Strong 自动禁用：未见（未匹配 `Strong fusion disabled`）。
- `corr_pairs==0`：当前日志未逐 step 输出 `corr_pairs` 标量，无法直接做时间序列核验；但 strong 加载成功且训练全程完成。
- 时间口径（full run）：
  - 首步约 `3.40s/it`（warm-up）
  - 总耗时 `123.5s`（`600 step`），均值约 `0.206s/step`
- 关键产物：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600/videos/traj_4d_step599.mp4`
  - `outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_600/stats/val_step0599.json`
  - `outputs/protocol_v1/gate1/selfcap_bar_8cam60f/ours_strong_600/stats/test_step0599.json`
  - `outputs/report_pack/metrics.csv`（含 gate1 条目）

## 5) 指标与结论（Stoploss）

full run（strong）：
- val@599：PSNR `18.4904` / SSIM `0.6438` / LPIPS `0.4195`
- test@599：PSNR `19.0478` / SSIM `0.6643` / LPIPS `0.4037` / tLPIPS `0.0232`

对照（已有 gate1 参考）：
- `gate1_selfcap_baseline_600` val PSNR `18.9106`
- `gate1_selfcap_ours_weak_600` val PSNR `18.7934`

结论：**本轮建议 stoploss（暂停继续加大 strong 投入）**。  
依据：
- 在同场景同预算下，strong 的 val 指标未超过 baseline/weak，且存在明显差距。
- 虽然训练稳定、流程可复现、证据齐全，但当前收益不足以支撑继续大规模 strong sweep。

下一步建议：
1. 主线继续沿 weak 融合推进 midterm 交付。  
2. strong 保留为后备分支，仅在补齐 `corr_pairs` 监控口径或改进对应质量后再重启小预算验证。
