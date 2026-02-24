# Feature Loss V1 Attempt (SelfCap bar canonical)

日期：`2026-02-24`  
协议：`docs/protocol.yaml` (`selfcap_bar_8cam60f_protocol_v1`)  
分支：`owner-b-20260224-vggt-feature-loss-v1`

## 1) Cache 与运行配置

- GT cache 脚本：`scripts/precompute_vggt_cache.py`
- cache tag：`selfcap_bar_8cam60f_depth_f0_n60_cam8_ds4`
- cache 产物：
  - `outputs/vggt_cache/selfcap_bar_8cam60f_depth_f0_n60_cam8_ds4/gt_cache.npz`
  - `outputs/vggt_cache/selfcap_bar_8cam60f_depth_f0_n60_cam8_ds4/meta.json`
- cache 关键 meta：
  - `phi_name=depth`
  - `phi.shape=(60,8,1,129,129)`
  - `input_size=(518,518)`
  - `phi_size=(129,129)`
  - `vggt_mode=crop`

新增 runner：`scripts/run_train_feature_loss_selfcap.sh`

## 2) Short sanity (200 steps)

命令（GPU1）：

```bash
DATA_DIR=/root/autodl-tmp/projects/4d-recon/data/selfcap_bar_8cam60f \
GPU=1 MAX_STEPS=200 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_sanity200 \
LAMBDA_VGGT_FEAT=0.05 \
VGGT_FEAT_EVERY=8 \
VGGT_FEAT_START_STEP=0 \
bash scripts/run_train_feature_loss_selfcap.sh
```

结果：
- 训练稳定，无 loss 爆炸/NaN。
- test@200：`PSNR=12.4811`, `SSIM=0.2931`, `LPIPS=0.6243`, `tLPIPS=0.0798`。
- 吞吐（以 `train_step*.json` 的 `ellipse_time` 近似）：
  - baseline@600: `26.2947/600 = 0.04382 s/step`
  - feature@200: `15.2576/200 = 0.07629 s/step`
  - 速率比：`1.74x`（<2x，满足止损线）

## 3) Full600 实验与对比

已存在对照（未重跑）：
- baseline：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600`
- control：`outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600`

### Run A: feature_loss_v1_600（主配置）

命令要点：
- `LAMBDA_VGGT_FEAT=0.05`
- `VGGT_FEAT_EVERY=8`
- `VGGT_FEAT_START_STEP=0`

目录：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600`

test@600：
- `PSNR=16.0347`
- `SSIM=0.6061`
- `LPIPS=0.4927`
- `tLPIPS=0.0443`

相对 baseline（test@600）：
- `ΔPSNR=-2.9149`
- `ΔSSIM=-0.0592`
- `ΔLPIPS=+0.0879`（变差）
- `ΔtLPIPS=+0.0213`（变差）

吞吐比：
- `46.6077/600 = 0.07768 s/step`
- 相对 baseline：`1.77x`（<2x，但质量显著退化）

### Run B: feature_loss_v1_retry_lam0.005_s200_600（止损调参）

命令要点：
- `LAMBDA_VGGT_FEAT=0.005`
- `VGGT_FEAT_EVERY=8`
- `VGGT_FEAT_START_STEP=200`

目录：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_retry_lam0.005_s200_600`

test@600：
- `PSNR=19.0555`
- `SSIM=0.6644`
- `LPIPS=0.4054`
- `tLPIPS=0.0239`

相对 baseline（test@600）：
- `ΔPSNR=+0.1059`（未达 +0.2 dB 成功线）
- `ΔSSIM=-0.0008`
- `ΔLPIPS=+0.0006`（未达 -0.01 成功线）
- `ΔtLPIPS=+0.0010`（未达 -10% 成功线，且略变差）

吞吐比：
- `41.8266/600 = 0.06971 s/step`
- 相对 baseline：`1.59x`（<2x）

## 4) 与 control 的对照观察

control (`control_weak_nocue_600`) test@600：
- `PSNR=19.1099`, `SSIM=0.6674`, `LPIPS=0.4033`, `tLPIPS=0.0236`

Run B 与 control 对比仍不占优（PSNR/SSIM/LPIPS/tLPIPS 均未超过 control）。

## 5) 成功线与止损判定

成功线（任一满足即可）：
- `tLPIPS` 下降 ≥ 10%
- 或 `LPIPS` 下降 ≥ 0.01
- 或 `PSNR` +0.2 dB

判定：
- Run A：不满足，且明显退化。
- Run B：不满足（2 次 full run 均无正向趋势）。

结论：**触发止损**。当前 v1（depth feature metric loss）在 canonical protocol 下未形成可辩护收益，建议暂停继续加算力，进入失败分析与下一轮设计（例如更稳健的 gating/phi 选择/对齐方式）后再试。
