# Handoff Plan-B seg2 (Owner A)

- Date: 2026-02-26
- Scope: `~/docs/plans/2026-02-26-owner-a-planb-seg2-anti-cherrypick.md`

## 1) 关键输出目录（必须路径）

- `outputs/plan_b/selfcap_bar_8cam60f_seg200_260/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f_seg200_260/velocity_stats.json`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_smoke200`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_smoke200`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600`

## 2) Gate 结果

- Gate-S1（init 质量门）：PASS
  - `match_ratio_over_eligible = 0.5923`
  - `clip_threshold(seg2)/clip_threshold(canonical) = 1.0072x`
- Gate-S2（smoke200 对比门）：PASS
  - baseline_smoke200 -> planb_init_smoke200
  - `ΔPSNR=+0.2042 dB`, `ΔLPIPS=-0.0530`, `ΔtLPIPS=-0.0524`（相对下降 60.8%）

## 3) full600 预算状态

- 本计划已执行（消耗最后 1 次）：
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600`
- 当前 7 天窗口 full600 预算（N=3）状态：**已用尽（剩余 0）**

## 4) 写作可引用结论

- seg2 smoke200：Plan-B init 对 baseline 有稳定提升趋势（PSNR↑, LPIPS↓, tLPIPS↓）。
- seg2 full600：`planb_init_600` 相对 `baseline_600` 明显提升：
  - `ΔPSNR=+1.9950`
  - `ΔSSIM=+0.0303`
  - `ΔLPIPS=-0.0604`
  - `ΔtLPIPS=-0.01564`

## 5) 对应 notes

- `notes/planb_seg2_preflight_owner_a.md`
- `notes/planb_seg2_gate_s1_owner_a.md`
- `notes/planb_seg2_gate_s2_owner_a.md`
- `notes/anti_cherrypick_seg200_260.md`
