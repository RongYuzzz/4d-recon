# Plan-B + Weak Synergy Smoke200 结论（Owner A）

- 日期：2026-02-26
- 计划：`~/docs/plans/2026-02-26-owner-a-planb-plus-weak-smoke200-and-go-nogo.md`
- 约束：仅 `MAX_STEPS=200`，未新增 full600 预算

## 关键产物路径（test@step199）

- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200/stats/test_step0199.json`

## Smoke200 指标（test@199）

| run | PSNR | LPIPS | tLPIPS |
|---|---:|---:|---:|
| planb_init_smoke200 | 12.8383 | 0.5796 | 0.03352 |
| planb_control_weak_nocue_smoke200 | 12.8384 | 0.5798 | 0.03405 |
| planb_ours_weak_smoke200_w0.3_end200 | 12.8439 | 0.5792 | 0.03377 |

## 相对 `planb_init_smoke200` 的增量

| run | ΔPSNR | ΔLPIPS | ΔtLPIPS |
|---|---:|---:|---:|
| planb_control_weak_nocue_smoke200 | +0.00010 | +0.00023 | +0.00053 |
| planb_ours_weak_smoke200_w0.3_end200 | +0.00558 | -0.00033 | +0.00025 |

## 结论（Go/No-Go）

**No-Go（当前不建议为 “Plan-B + weak cue” 申请新增 1 次 full600）**：本次仅观察到非常小的 PSNR/LPIPS 改善且 `tLPIPS` 未同向改善；触发条件为后续在相同协议下补充多 seed smoke200（建议 ≥3）并满足 `ΔPSNR >= +0.01`、`ΔLPIPS <= -0.001`、`ΔtLPIPS <= 0` 后再发起扩预算决议。

