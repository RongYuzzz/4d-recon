# seg200_260 control_weak_nocue_600 (Owner A)

- Date: 2026-02-26
- Dataset: `data/selfcap_bar_8cam60f_seg200_260`

## Baseline验收

Verified existing artifacts (no rerun):
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/stats/test_step0599.json`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/videos/traj_4d_step599.mp4`

## control_weak_nocue_600 执行

Command:
- `GPU=0 MAX_STEPS=600 DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 CUE_TAG=selfcap_bar_8cam60f_seg200_260_zeros_control RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600 bash scripts/run_train_control_weak_nocue_selfcap.sh`

Verified artifacts:
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600/stats/test_step0599.json`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600/videos/traj_4d_step599.mp4`

## Test@599 指标对比

- seg2 baseline_600:
  - PSNR `18.0467529297`
  - SSIM `0.6353095770`
  - LPIPS `0.4138190150`
  - tLPIPS `0.0234328471`
- seg2 control_weak_nocue_600:
  - PSNR `18.1969337463`
  - SSIM `0.6369218230`
  - LPIPS `0.4157035947`
  - tLPIPS `0.0221871883`

Delta (control - baseline):
- `ΔPSNR = +0.1501808167 dB`
- `ΔSSIM = +0.0016122460`
- `ΔLPIPS = +0.0018845797` (slightly worse)
- `ΔtLPIPS = -0.0012456588` (better)

一句话结论：**在 seg2 上，control_weak_nocue 相比 baseline 呈现“时序指标改善（tLPIPS↓）且 PSNR/SSIM 略升、LPIPS 微弱变差”的同向趋势，可作为 anti-cherrypick 防守证据位。**
