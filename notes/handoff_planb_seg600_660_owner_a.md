# Handoff: Plan-B seg600_660 smoke200 (Owner A -> Owner B)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600`
- Plan: `~/docs/plans/2026-02-26-owner-a-planb-seg600-smoke200-and-handoff.md`

## Summary

- A91/A92/A93 completed; Gate-S1 PASS.
- A94 smoke200 completed for both baseline and planb; Gate-S2 PASS.
- No new full600 run was executed (budget guard respected).

## Required reference paths (for report-pack/writeup refresh)

- `outputs/plan_b/selfcap_bar_8cam60f_seg600_660/velocity_stats.json`
- `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/baseline_smoke200/`
- `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/planb_init_smoke200/`
- `notes/anti_cherrypick_seg600_660.md`

## Gate outcomes

- Gate-S1:
  - `match_ratio_over_eligible = 0.5863`
  - clip threshold ratio vs canonical = `1.0493x`
  - verdict: PASS
- Gate-S2 (`test_step0199`):
  - baseline: PSNR `12.5847`, LPIPS `0.6268`, tLPIPS `0.08639`
  - planb: PSNR `12.7752`, LPIPS `0.5779`, tLPIPS `0.03387`
  - deltas (planb - baseline): `+0.1905 / -0.0488 / -0.0525`
  - verdict: PASS (condition 1 and 2 both satisfied)

## Notes for Owner B

- This segment adds a farther anti-cherrypick slice (`frame_start=600`) without consuming full600 budget.
- Trend remains aligned with previous slices; can be appended directly to Plan-B defense narrative.
