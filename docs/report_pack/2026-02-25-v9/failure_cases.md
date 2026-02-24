# Failure Cases (Midterm, 2026-02-24, Protocol v1)

本文件用于汇报中的“失败案例/机理解释”，随 `scripts/pack_evidence.py` 打包（`outputs/report_pack/`）。

## Case 1: 短预算 + 稀疏几何导致点云塌缩（gs8@200）

- 现象：`outputs/sweep_selfcap_baseline_gs8/videos/traj_4d_step199.mp4` 在中段帧呈现“主体几乎消失，仅剩稀疏亮点”的塌缩画面。
- 机制推测：
  - triangulation 初值在暗背景区域本就稀疏；
  - 仅训练 200 steps 时 relocation/优化不足；
  - `KEYFRAME_STEP=5` 下跨帧误差被放大，导致可见几何退化为稀疏噪点。
- 复现命令：
```bash
cd /root/projects/4d-recon
ffmpeg -y -i outputs/sweep_selfcap_baseline_gs8/videos/traj_4d_step199.mp4 \
  -vf "select='eq(n,20)'" -vframes 1 \
  outputs/report_pack/failure_viz/case1_gs8_density_collapse.png
```
- 证据路径：
  - 视频：`outputs/sweep_selfcap_baseline_gs8/videos/traj_4d_step199.mp4`
  - 截图：`outputs/report_pack/failure_viz/case1_gs8_density_collapse.png`

## Case 2: baseline600 动态前景拖影/重影（Protocol v1）

- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4` 可见前景边界出现雾状拖影，轮廓不稳定。
- 机制推测：
  - 快速运动与遮挡交替时，线性运动假设 + 时间归一化插值会在边界处产生时序错配；
  - 固定相机轨迹渲染下该错配表现为连续帧“雾化重影”。
- 复现命令：
```bash
cd /root/projects/4d-recon
ffmpeg -y -i outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4 \
  -vf "select='eq(n,40)'" -vframes 1 \
  outputs/report_pack/failure_viz/case2_baseline_motion_smear.png
```
- 证据路径：
  - 视频：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4`
  - 截图：`outputs/report_pack/failure_viz/case2_baseline_motion_smear.png`

## Case 3: ours-weak600 仍有残余拖影（Protocol v1）

- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/videos/traj_4d_step599.mp4` 中前景边界仍可见残余拖影，未形成“质变式”改善。
- 机制推测：
  - 当前 cue mining 为 diff fallback，mask 主要反映“帧差分动态性”，对跨帧几何错配本身约束不足；
  - 弱融合本质上是 photometric reweighting，无法直接修正多视角三角化/速度场的系统性偏差。
- 复现命令：
```bash
cd /root/projects/4d-recon
ffmpeg -y -i outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/videos/traj_4d_step599.mp4 \
  -vf "select='eq(n,40)'" -vframes 1 \
  outputs/report_pack/failure_viz/case3_weak_residual_smear.png
```
- 证据路径：
  - 视频：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/videos/traj_4d_step599.mp4`
  - 截图：`outputs/report_pack/failure_viz/case3_weak_residual_smear.png`

## Case 4: ours-strong600 未形成稳定优势（Protocol v1, stoploss）

- 现象：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600/videos/traj_4d_step599.mp4` 相比 weak/baseline 未呈现稳定可辩护的视觉优势（在本轮参数与预算下）。
- 机制推测：
  - KLT 对应属于“局部、稀疏、易受遮挡影响”的信号；
  - corr loss 只在 early steps（`TEMPORAL_CORR_END_STEP=200`）生效，信号不足以抵消三角化噪声与动态区域误差；
  - 更强的 corr 权重会带来不稳定风险（需额外 stoploss 审计）。
- 复现命令：
```bash
cd /root/projects/4d-recon
ffmpeg -y -i outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600/videos/traj_4d_step599.mp4 \
  -vf "select='eq(n,40)'" -vframes 1 \
  outputs/report_pack/failure_viz/case4_strong_no_gain.png
```
- 证据路径：
  - 视频：`outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_600/videos/traj_4d_step599.mp4`
  - 截图：`outputs/report_pack/failure_viz/case4_strong_no_gain.png`
  - matching 可视化：`outputs/correspondences/selfcap_bar_8cam60f_klt/viz`

