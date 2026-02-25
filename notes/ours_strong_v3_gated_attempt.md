# Ours-Strong v3 Gated Attempt (Owner B)

日期：2026-02-25
分支：`owner-b-20260225-strong-v3`

## 1. 本轮改动（B42）

已实现两个默认关闭的新开关（不影响既有 baseline/weak/strong）：

- `temporal_corr_gate_pseudo_mask: bool = False`
  - 在 `_compute_temporal_corr_loss()` 中对每条 correspondence 权重执行：
  - `w = w * (1 - dynamicness(src_xy))`
- `temporal_corr_pred_pred_detach_target: bool = False`
  - 当 `temporal_corr_loss_mode=pred_pred` 时，对 `target` 执行 `.detach()`（可选）

脚本透传新增：

- `TEMPORAL_CORR_GATE_PSEUDO_MASK`（默认 `0`）
- `TEMPORAL_CORR_PRED_PRED_DETACH_TARGET`（默认 `0`）
- CLI: `--temporal-corr-gate-pseudo-mask`、`--temporal-corr-pred-pred-detach-target`

安全降级（按要求）：

- 若开启 `temporal_corr_gate_pseudo_mask` 但 pseudo mask 未加载，则打印一次 warning 并自动禁用 gate。

契约测试：

```bash
python3 scripts/tests/test_strong_fusion_flags.py
python3 scripts/tests/test_temporal_correspondences_klt_contract.py
python3 scripts/tests/test_run_pipeline_env_flags.py
```

结果：全部 PASS。

## 2. 200-step sanity（B43）

固定条件：`DATA_DIR=/root/projects/4d-recon/data/selfcap_bar_8cam60f`，`START_FRAME=0 END_FRAME=60`，`KEYFRAME_STEP=5 GLOBAL_SCALE=6 SEED=42`，`GPU=1`。

### Run A: `pred_pred + detach + gate`

```bash
GPU=1 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/sweeps/selfcap_bar_strong_v3_gate1_detach1_predpred_s200 \
TEMPORAL_CORR_LOSS_MODE=pred_pred TEMPORAL_CORR_GATE_PSEUDO_MASK=1 \
TEMPORAL_CORR_PRED_PRED_DETACH_TARGET=1 LAMBDA_CORR=0.01 \
TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

产物：

- `outputs/sweeps/selfcap_bar_strong_v3_gate1_detach1_predpred_s200/stats/test_step0199.json`
- `outputs/sweeps/selfcap_bar_strong_v3_gate1_detach1_predpred_s200/videos/traj_4d_step199.mp4`

指标（test@199）：

- PSNR `12.6117`
- SSIM `0.3060`
- LPIPS `0.6304`
- tLPIPS `0.08723`
- 总时长约 `73.6s`（约 `0.368s/step`）

肉眼现象：无 NaN/崩溃，轨迹视频可正常输出，动态区域仍有轻微时序抖动。

### Run B: `pred_pred + no_detach + gate`

```bash
GPU=1 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/sweeps/selfcap_bar_strong_v3_gate1_detach0_predpred_s200 \
TEMPORAL_CORR_LOSS_MODE=pred_pred TEMPORAL_CORR_GATE_PSEUDO_MASK=1 \
TEMPORAL_CORR_PRED_PRED_DETACH_TARGET=0 LAMBDA_CORR=0.01 \
TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

产物：

- `outputs/sweeps/selfcap_bar_strong_v3_gate1_detach0_predpred_s200/stats/test_step0199.json`
- `outputs/sweeps/selfcap_bar_strong_v3_gate1_detach0_predpred_s200/videos/traj_4d_step199.mp4`

指标（test@199）：

- PSNR `12.6121`
- SSIM `0.3063`
- LPIPS `0.6296`
- tLPIPS `0.08667`
- 总时长约 `76.2s`（约 `0.381s/step`）

肉眼现象：同样稳定，无明显崩溃；与 Run A 观感接近。

结论（B44 选型）：Run B 的 `tLPIPS/LPIPS` 略优，选 `detach=0` 跑 full600。

## 3. full600（B44）

```bash
GPU=1 MAX_STEPS=600 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600 \
TEMPORAL_CORR_LOSS_MODE=pred_pred TEMPORAL_CORR_GATE_PSEUDO_MASK=1 \
TEMPORAL_CORR_PRED_PRED_DETACH_TARGET=0 LAMBDA_CORR=0.01 \
TEMPORAL_CORR_END_STEP=200 TEMPORAL_CORR_MAX_PAIRS=200 \
bash scripts/run_train_ours_strong_selfcap.sh
```

产物检查：

- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/stats/test_step0599.json`（存在，含 `tlpips`）
- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/videos/traj_4d_step599.mp4`（存在）

指标（test@599）：

- PSNR `18.9491`
- SSIM `0.6652`
- LPIPS `0.4072`
- tLPIPS `0.02281`
- 总时长约 `104.8s`

## 4. 止损判定（B45）

对比基线 `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/stats/test_step0599.json`：

- weak: PSNR `19.0194`, LPIPS `0.4037`, tLPIPS `0.02308`
- strong_v3: PSNR `18.9491`, LPIPS `0.4072`, tLPIPS `0.02281`

差值（strong_v3 相对 weak）：

- `tLPIPS` 下降约 `1.19%`（未达到 ≥10%）
- `LPIPS` 反而上升约 `+0.00356`（未达到下降 ≥0.01）
- `PSNR` 下降约 `-0.070 dB`（未达到提升 ≥0.2 dB）

结论：触发止损，**不再继续 strong v3 扩展试验**。

## 5. 失败交付证据（B45）

- correspondence 可视化（示例）：
  - `outputs/correspondences/selfcap_bar_8cam60f_klt/viz/frame000000_to_000001_cam02.jpg`
- 训练日志关键信息：
  - 200-step 与 600-step 训练均无 NaN/崩溃；评测与视频产物完整。
- 一句话归因：
  - `pseudo-mask gate` 对动态污染有轻微抑制（tLPIPS 小幅下降），但不足以转化为可辩护的整体收益，且静态重建质量（PSNR/LPIPS）出现轻微退化。
