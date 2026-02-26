# Feature-Loss v2 梯度链检查（Owner A, GPU0, 2026-02-26）

## 1. 执行目标

- 依据 `~/docs/plans/2026-02-26-owner-a-featureloss-gradchain-and-postfix-expose.md` 执行 A83：`MAX_STEPS=10` 诊断小跑，验证 feature-loss 梯度链路是否存在且数值有限。

## 2. 执行命令（按计划原样）

```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py

DATA_DIR=data/selfcap_bar_8cam60f
INIT_NPZ=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz
CACHE_NPZ=.worktrees/owner-a-20260226-v2-postfix/outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz

OUT_TMP=/tmp/feature_loss_v2_grad10
mkdir -p "$OUT_TMP"

# 10-step: isolate feature-loss as much as possible (disable other loss weights).
CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$INIT_NPZ" \
  --result-dir "$OUT_TMP" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 10 \
  --eval-steps 10 \
  --save-steps 10 \
  --seed 42 \
  --train-camera-names 02,03,04,05,06,07 \
  --val-camera-names 08 \
  --test-camera-names 09 \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --lambda-img 0 \
  --lambda-ssim 0 \
  --lambda-perc 0 \
  --lambda-4d-reg 0 \
  --lambda-duration-reg 0 \
  --vggt-feat-cache-npz "$CACHE_NPZ" \
  --lambda-vggt-feat 0.01 \
  --vggt-feat-loss-type cosine \
  --vggt-feat-every 1 \
  --vggt-feat-phi-name token_proj \
  --vggt-feat-gating none \
  --t0-debug-interval 1 \
  --t0-grad-log-path outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv
```

执行注记：
- 首次运行在 `gsplat` 动态编译阶段报 `RuntimeError: Ninja is required...`。
- 环境修正为仅补充 venv 可执行路径（`export PATH=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin:$PATH`）后，复跑同一 10-step 命令成功。

## 3. 梯度 CSV 摘要（前 10 个 step）

文件：`outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv`

| step | vel_grad_norm | duration_grad_norm | vel_grad_finite | duration_grad_finite |
|---:|---:|---:|---:|---:|
| 0 | 2.0945619792e-02 | 1.8965738127e-04 | 1 | 1 |
| 1 | 6.2547698617e-02 | 4.4680832070e-04 | 1 | 1 |
| 2 | 5.9172004461e-02 | 3.8498878712e-04 | 1 | 1 |
| 3 | 4.2853847146e-02 | 3.5407161340e-04 | 1 | 1 |
| 4 | 3.1600050628e-02 | 2.2477051243e-04 | 1 | 1 |
| 5 | 3.3856980503e-02 | 3.3473916119e-04 | 1 | 1 |
| 6 | 2.2616362199e-02 | 1.9600157975e-04 | 1 | 1 |
| 7 | 4.1986066848e-02 | 2.8113988810e-04 | 1 | 1 |
| 8 | 2.3314198479e-02 | 2.0776614838e-04 | 1 | 1 |
| 9 | 2.7755515650e-02 | 2.1854198712e-04 | 1 | 1 |

核验摘要：
- `vel_grad_norm` 在 step 0~9 均为非 0。
- `duration_grad_norm` 在 step 0~9 均为非 0。
- `vel_grad_finite=1` 且 `duration_grad_finite=1`（全程有限值）。

## 4. 一句话结论

在 `feature_loss_v2` 的 10-step 诊断小跑中，梯度链路存在，且在 `velocities/durations` 参数上表现为持续非零并保持 finite。
