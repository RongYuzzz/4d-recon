# protocol_v2 static/dynamic τ selection（planb_feat_v2_full600_start300）

## 输入依据

- 速度统计：`notes/velocity_stats_planb_feat_v2_full600_start300.md`
  - `p50 = 0.075432`
  - `p90 = 0.139066`
- checkpoint：
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt`

## A/B 阈值设置

- `τ_low = 0.075432`（p50）
- `τ_high = 0.139066`（p90）

导出日志（`[Export] applied export_vel_filter ... kept ...`）：
- static @ `τ_low`: `46374/92749 (0.500)`
- dynamic @ `τ_low`: `46375/92749 (0.500)`
- static @ `τ_high`: `83473/92749 (0.900)`
- dynamic @ `τ_high`: `9276/92749 (0.100)`

## 导出视频路径

- static `τ_low`:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.075432/videos/traj_4d_step599.mp4`
- dynamic `τ_low`:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.075432/videos/traj_4d_step599.mp4`
- static `τ_high`:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.139066/videos/traj_4d_step599.mp4`
- dynamic `τ_high`:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.139066/videos/traj_4d_step599.mp4`

## 最终选择

- `τ_final = 0.139066`（p90）

理由：
- static 层保留 90% Gaussians，更接近“背景主导层”，用于展示可编辑背景更稳。
- dynamic 层压缩到 10%，运动主体更集中，作为 object-level 编辑入口更清晰。

## 失败边界（必须声明）

- 在 `τ_final` 下，低速/缓慢运动区域更容易被并入 static 层（slow-motion 漏检）。
- 在 `τ_low` 下，dynamic 覆盖过大（50%），会把部分背景抖动带入动态层，降低可编辑性边界清晰度。

