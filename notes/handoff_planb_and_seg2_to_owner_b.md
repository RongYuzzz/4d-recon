# Handoff: Plan-B + seg2 control to Owner B

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb`

## 1) 可直接打包/写作引用路径

必含路径（已验收）：
- `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600`

补充路径（便于写作）：
- `outputs/report_pack/metrics.csv`
- `outputs/report_pack/scoreboard_smoke200.md`
- `outputs/report_pack/scoreboard.md`
- `notes/planb_preflight_owner_a.md`
- `notes/planb_gate_b1_owner_a.md`
- `notes/planb_gate_b2_owner_a.md`
- `notes/seg2_control_weak_nocue_600_owner_a.md`
- `notes/anti_cherrypick_seg200_260.md`

## 2) 本轮 full600 预算消耗

按 2026-02-26 决议 7 天预算 `N=3` 计：
- 本轮新增 full600（已执行）：
  - `planb_init_600`（1 次）
  - `seg2_control_weak_nocue_600`（1 次）
- `seg200_260 baseline_600`：已存在，未重跑（0 次新增）

合计本轮新增：`2 / 3`
未来 7 天可用剩余：`1 / 3`

## 3) 结论摘要（供写作入口）

- Gate-B1：通过（planb smoke200 相比 baseline_smoke200，PSNR/LPIPS/tLPIPS 全部改善）。
- Gate-B2：Go（`planb_init_600` 对 `baseline_600`：PSNR +1.499 dB，tLPIPS -68.66%）。
- seg2 防守位：`control_weak_nocue_600` 已补齐，趋势为 tLPIPS 改善、PSNR/SSIM 略升、LPIPS 微弱变差。
