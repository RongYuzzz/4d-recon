# Plan-B 组件消融（smoke200, Owner A）

- 日期：2026-02-26
- 计划：`~/docs/plans/2026-02-26-owner-a-planb-component-ablation-smoke200.md`
- 约束：仅 `MAX_STEPS=200`，未新增 full600
- 数据：`data/selfcap_bar_8cam60f`（protocol_v1 canonical）

## 执行概览

1. A71 预检通过：
   - `python3 scripts/tests/test_pack_evidence.py`
   - `python3 scripts/tests/test_build_report_pack.py`
   - `python3 scripts/tests/test_summarize_scoreboard.py`
   - `test -d data/selfcap_bar_8cam60f/triangulation`
2. A72 生成三类 init 变体并验收产物：
   - `outputs/plan_b_ablation/selfcap_bar_8cam60f/no_drift/`
   - `outputs/plan_b_ablation/selfcap_bar_8cam60f/no_mutual/`
   - `outputs/plan_b_ablation/selfcap_bar_8cam60f/clip_p95/`
   - 每个目录均包含 `init_points_planb_step5.npz` 与 `velocity_stats.json`
3. A73 训练三条 smoke200 变体，全部稳定完成到 step199（无 NaN/发散）。

## Init 统计（机制侧）

| 变体 | mutual_nn | drift_removal | clip_q | clip_threshold (m/frame) | match_ratio_over_eligible | n_clipped |
|---|---:|---:|---:|---:|---:|---:|
| default | True | True | 0.99 | 0.010881 | 0.6029 | 514 |
| no_drift | True | False | 0.99 | 0.010872 | 0.6029 | 514 |
| no_mutual | False | True | 0.99 | 0.022703 | 0.9992 | 852 |
| clip_p95 | True | True | 0.95 | 0.005705 | 0.6029 | 2570 |

## Smoke200 指标（test@199）

| run | PSNR | LPIPS | tLPIPS | ΔPSNR vs default | ΔLPIPS vs default | ΔtLPIPS vs default |
|---|---:|---:|---:|---:|---:|---:|
| baseline_smoke200_planb_window | 12.6350 | 0.6297 | 0.0877 | -0.2033 | +0.0502 | +0.0542 |
| planb_init_smoke200 (default) | 12.8383 | 0.5796 | 0.0335 | +0.0000 | +0.0000 | +0.0000 |
| planb_ablate_no_drift_smoke200 | 12.8481 | 0.5794 | 0.0341 | +0.0098 | -0.0002 | +0.0005 |
| planb_ablate_no_mutual_smoke200 | 12.7849 | 0.5892 | 0.0470 | -0.0534 | +0.0097 | +0.0135 |
| planb_ablate_clip_p95_smoke200 | 12.8411 | 0.5791 | 0.0329 | +0.0028 | -0.0005 | -0.0006 |

## Throughput 摘要（step199）

| run | iter_per_sec | elapsed_sec |
|---|---:|---:|
| baseline_smoke200_planb_window | 18.8900 | 10.5876 |
| planb_init_smoke200 (default) | 19.8823 | 10.0592 |
| planb_ablate_no_drift_smoke200 | 35.2686 | 5.6708 |
| planb_ablate_no_mutual_smoke200 | 39.0894 | 5.1165 |
| planb_ablate_clip_p95_smoke200 | 38.9707 | 5.1321 |

- 说明：该表用于效率与止损观察（是否出现异常慢/卡住）；方法优劣判定仍以 PSNR/LPIPS/tLPIPS 为主。

## 结论（可用于写作）

- **mutual NN 是关键组件**：禁用后（`no_mutual`）相对 default 出现一致退化，`tLPIPS +0.0135`、`LPIPS +0.0097`、`PSNR -0.0534`。
- 在该 canonical smoke200 窗口内，`drift_removal` 与 `clip 0.99->0.95` 对终点指标敏感度较小，未观察到显著负面影响。
- 因此当前最稳健的“必要性”证据可聚焦于：**mutual NN 对 Plan-B 收益贡献显著；其余两项更像稳定性/鲁棒性调节项**。
