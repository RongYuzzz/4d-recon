# Ablation Notes (Plan-B Defense v23, 2026-02-26)

本文件为 Writing Mode 收口版，汇总 Plan-B 主线证据、anti-cherrypick 切片与组件消融（smoke200）。
v22 之后继续追加 seg600_660（或 fallback 的 seg300_360）防守位证据。

## 协议与约束

- 协议固定：`docs/protocol.yaml` (`protocol_v1`)
- 不改 `data/`、不改帧段/相机划分/`global_scale`/`keyframe_step`
- feature-loss 主线冻结：不再新增 full600，仅保留 No-GPU 归因材料

## Canonical 关键对比（test@step599）

| Run | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: |
| baseline_600 | 18.9496 | 0.6653 | 0.4048 | 0.0230 |
| control_weak_nocue_600 | 19.1099 | 0.6674 | 0.4033 | 0.0236 |
| planb_init_600 | 20.4488 | 0.7070 | 0.3497 | 0.0072 |

读法：Plan-B 在 canonical 上同时提升 PSNR/SSIM，并显著降低 LPIPS/tLPIPS。

## seg200_260 anti-cherrypick（test）

| Run | Step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.7162 | 0.3176 | 0.6349 | 0.0862 |
| planb_init_smoke200 | 199 | 12.9204 | 0.3206 | 0.5819 | 0.0338 |
| baseline_600 | 599 | 18.0468 | 0.6353 | 0.4138 | 0.0234 |
| control_weak_nocue_600 | 599 | 18.1969 | 0.6369 | 0.4157 | 0.0222 |
| planb_init_600 | 599 | 20.0417 | 0.6656 | 0.3534 | 0.0078 |

## seg400_460 anti-cherrypick（smoke200，test@step199）

| Run | Step | PSNR | SSIM | LPIPS | tLPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_smoke200 | 199 | 12.5889 | 0.2981 | 0.6277 | 0.08518 |
| planb_init_smoke200 | 199 | 12.7610 | 0.3073 | 0.5839 | 0.03527 |

Delta（planb - baseline）：
- ΔPSNR `+0.1721`
- ΔLPIPS `-0.0438`
- ΔtLPIPS `-0.04990`（相对 `-58.59%`）

## Plan-B 组件消融（smoke200，canonical）

来源：`notes/planb_component_ablation_smoke200_owner_a.md`

| Run | PSNR | LPIPS | tLPIPS | ΔPSNR vs default | ΔLPIPS vs default | ΔtLPIPS vs default |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| planb_init_smoke200 (default) | 12.8383 | 0.5796 | 0.0335 | +0.0000 | +0.0000 | +0.0000 |
| planb_ablate_no_drift_smoke200 | 12.8481 | 0.5794 | 0.0341 | +0.0098 | -0.0002 | +0.0005 |
| planb_ablate_clip_p95_smoke200 | 12.8411 | 0.5791 | 0.0329 | +0.0028 | -0.0005 | -0.0006 |
| planb_ablate_no_mutual_smoke200 | 12.7849 | 0.5892 | 0.0470 | -0.0534 | +0.0097 | +0.0135 |

结论（写作入口）：
- **必要补丁是 mutual NN**：禁用 mutual（`no_mutual`）后出现一致退化，尤其 `tLPIPS` 明显变差。
- `no_drift` 与 `clip_p95` 在该 smoke200 窗口内对终点指标影响较小，更接近鲁棒性调节项。

## 写作口径（可直接复用）

- Plan-B 不改变协议分布项，只替换初始化速度来源（triangulation -> 3D velocity init）。
- Plan-B 解决的是 velocity prior 的质量/尺度/一致性不足或噪声过大，不是“速度为 0 已被证实”。

## Plan-B + weak（smoke200）

- 三行对比入口：`planb_init_smoke200` / `planb_control_weak_nocue_smoke200` / `planb_ours_weak_smoke200_w0.3_end200`。
- 结论入口：以 `notes/planb_plus_weak_smoke200_owner_a.md` 为主口径（并与 `outputs/report_pack/planb_plus_weak_smoke200.md` 对齐），当前不支持直接申请新增 full600 预算。
