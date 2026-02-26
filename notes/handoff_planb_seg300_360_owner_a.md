# Handoff: Plan-B seg300_360 smoke200 (Owner A -> Owner B)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300`
- Plan: `~/docs/plans/2026-02-26-owner-a-planb-seg300_360-smoke200-and-handoff.md`

## Summary

- A121-A127 completed.
- Gate-S1 PASS, Gate-S2 PASS.
- No new full600 run was executed (budget guard respected).

## Gate outcomes

- Gate-S1:
  - `match_ratio_over_eligible = 0.5956`
  - `clip_threshold_m_per_frame = 0.0115640901` (`1.0627x` vs canonical)
  - `n_clipped = 507`
  - verdict: PASS
- Gate-S2 (`test_step0199`):
  - baseline: PSNR `12.7535`, LPIPS `0.6218`, tLPIPS `0.08467`
  - planb: PSNR `12.9346`, LPIPS `0.5720`, tLPIPS `0.03297`
  - deltas (planb - baseline): `+0.1811 / -0.0497 / -0.0517`
  - verdict: PASS (condition 1 and 2 both satisfied)

## Required reference paths

- `/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/velocity_stats.json`
- `/root/projects/4d-recon/outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200/`
- `/root/projects/4d-recon/outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200/`
- `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4`
- `notes/anti_cherrypick_seg300_360.md`

## Notes for Owner B

- `scripts/summarize_planb_anticherrypick.py` 的 seg300 fallback 现在可替换为真实证据引用。
- 可在后续 report-pack/evidence 更新中将 seg300_360 与其他 slice 并列展示，进一步压缩 cherry-pick 攻击面。
