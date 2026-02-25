# Weak + VGGT Cue Probe（selfcap_bar_8cam60f）

## 对比对象

- Protocol v1 基线：
  - `baseline_600`
  - `control_weak_nocue_600`
  - `ours_weak_600`
- Probe：
  - `ours_weak_vggt_w0.3_end200_s200`（200-step）
  - `ours_weak_vggt_w0.3_end200_600`（600-step）

## Test 指标对比

| run | step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_600 | 599 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| control_weak_nocue_600 | 599 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| ours_weak_600 | 599 | 19.0194 | 0.6661 | 0.4037 | 0.0231 |
| ours_weak_vggt_w0.3_end200_s200 | 199 | 12.6319 | 0.3064 | 0.6306 | 0.0877 |
| ours_weak_vggt_w0.3_end200_600 | 599 | 18.9808 | 0.6651 | 0.4047 | 0.0245 |

数据来源：
- `outputs/protocol_v1/selfcap_bar_8cam60f/*/stats/test_step0599.json`
- `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_s200/stats/test_step0199.json`
- `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600/stats/test_step0599.json`

## 产物核对

- 200-step:
  - `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_s200/videos/traj_4d_step199.mp4`
  - `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_s200/stats/val_step0199.json`
  - `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_s200/stats/test_step0199.json`
- 600-step:
  - `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600/videos/traj_4d_step599.mp4`
  - `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600/stats/val_step0599.json`
  - `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/ours_weak_vggt_w0.3_end200_600/stats/test_step0599.json`

## 结论（是否值得开 protocol_v2）

- 结论：**NO**
- 理由（单句）：`ours_weak_vggt_w0.3_end200_600` 未优于 `ours_weak_600`/`control_weak_nocue_600`，且 tLPIPS 略高（0.0245 vs 0.0231/0.0236），暂无升级 protocol 的收益信号。
