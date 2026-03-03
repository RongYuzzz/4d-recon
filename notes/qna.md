# Q&A

## What is the data contract?

最小可用（能训练）：
- `data/<scene>/images/<cam>/*`（多相机图像；SelfCap canonical 产物已满足）
- `data/<scene>/sparse/0/{cameras.bin,images.bin,points3D.bin}`（COLMAP sparse）
- `data/<scene>/triangulation/points3d_frame*.npy` + `colors_frame*.npy`（每帧点云）

其中：
- `trainer` 需要 `images/ + sparse/0`（相机与投影）
- `combine_frames_fast_keyframes.py` 需要 `triangulation/`（初始化关键帧/速度）

## Why do we need an adapter?

因为公开数据集通常给的是“多视角视频/图片 + 相机参数（yml/json）”，不会按我们工程约定直接提供：
- `sparse/0/*.bin`（COLMAP 工程文件）
- `triangulation/*.npy`（每帧点云中间产物）

所以必须把“适配/生成中间产物”纳入正式入口，否则会一直卡在找数据样例上。

## What does T0 prove?

T0 是基底审计（Go/No-Go）：
- `force_zero_velocity` 能退化成静态（零速度测试）
- `velocities/durations` 的梯度存在且有限（非全 0 / 非 NaN）

结论：证明“时间参数化 + motion 参数 + 训练管线”是健康的，后续做更复杂的约束/融合才有意义。

---

## protocol_v2（双阶段）必问（短答案 + 证据指针）

### 1) baseline 是什么？`baseline_600` 的含义与路径？

- 含义：不引入 Plan‑B 速度初始化/阶段二语义约束的基线训练（用于计算 Δ 列与风险对照）。
- 路径：`outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/`
- 证据指针：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

### 2) stage‑2 当前 gate/止损结论是什么？证据在哪里？

- 结论：`planb_feat_v2_full600_lam0.005_warm100_ramp400` 命中 **PSNR↓ / LPIPS↑ / tLPIPS↑** 止损；`planb_feat_v2_full600_lam0.005_start300_ramp200_every16` 未触发硬止损（PSNR↑，但 LPIPS/tLPIPS 仍退步）。
- 口径：目前属于“最小正趋势但未形成全指标增益”，按预算纪律停止新增 full600 sweep，避免盲调参烧卡。
- 证据指针（对比表）：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- 证据指针（审计记录）：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

### 3) “端到端”到底怎么定义？是否依赖 2D 模型？

- 定义：**不依赖外部 2D 强监督前置**（如 SAM/DEVA 掩码或 tracker 轨迹）；VGGT 线索属于冻结 soft prior，以 loss/weight 注入优化。
- 证据指针（口径落盘）：`4D-Reconstruction-v2.md`
- 证据指针（协议约束）：`docs/protocols/protocol_v2.yaml`

### 4) 为什么用 SelfCap + tLPIPS（而不是开题里写的 mIoU/多数据集）？

- 取舍：阶段一证据链已冻结在 SelfCap 上；阶段二目标是“学术完善/可答辩”，优先补齐时序稳定（tLPIPS）与可编辑演示，再谈扩展数据集与分割指标。
- 证据指针（评测口径/不变量）：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- 证据指针（scoreboard）：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

### 5) 动静解耦 demo 的意义是什么？τ 怎么选？失败例在哪？

- 意义：把“可编辑性/对象移除”落到可视证据（static-only 背景与 dynamic-only 动态层），答辩时一眼可解释。
- 视频产物：
  - static-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
  - dynamic-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- τ 与失败例证据指针：`notes/velocity_stats_planb_init_600.md`、`notes/protocol_v2_static_dynamic_tau.md`

### 6) 为什么会出现 `PSNR↑` 但 `tLPIPS↑`？画面上对应什么现象？

- 短答：当前 `planb_feat_v2_full600_lam0.005_start300_ramp200_every16` 更偏向逐帧重建质量（PSNR），但跨帧一致性未同步改善（tLPIPS 上升）。
- 画面现象：side-by-side 中可见局部纹理更“锐”，但动态区域在邻帧间存在轻微闪烁/漂移。
- 证据指针：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`、`outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`

### 7) 为什么不继续 sweep full600？

- 短答：协议要求“先 smoke gate，再有限 full600”；当前已完成单次补跑并形成 mixed trend，不满足继续大规模 full600 的性价比。
- 决策依据：避免在未明确机理前盲目烧卡，优先做可解释诊断与约束设计修正。
- 证据指针：`docs/protocols/protocol_v2.yaml`（stoploss/预算纪律）、`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

### 8) stage‑2 trade-off 的最小证据包看哪三类材料？

- 定量：`docs/report_pack/2026-02-27-v2/scoreboard.md` + `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- 定性：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`、`outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`、`outputs/qualitative/planb_vs_baseline/baseline_vs_planbfeat_full600_step599.mp4`
- 导出：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`、`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`

### 9) 是否最终批准新增 full600？为什么？

- 短答：未批准。当前 stage‑2 在 full600 仍是 mixed trend（`PSNR` 单点改善但 `LPIPS/tLPIPS` 未同步改善），按预算纪律不再追加 full600。
- 决策依据：优先保留预算纪律与可审计收口，避免在机理未清前继续烧卡。
- 证据指针：`docs/report_pack/2026-02-27-v2/README.md`、`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

### 10) C2(noconf) full600 的结论是什么？证据在哪里？

- 短答：本轮未执行 C2(noconf) full600（预算未批），因此没有新增 full600 数值结论。
- 可用结论：`..._noconf` 目前仅有 smoke200 趋势证据（相对其他候选有更好的 tLPIPS），但不足以单独支撑 full600 外推。
- 证据指针：`docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`、`docs/report_pack/2026-02-27-v2/README.md`
