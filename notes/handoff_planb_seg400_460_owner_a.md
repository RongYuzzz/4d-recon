# Handoff: Plan-B seg400_460 smoke200 (Owner A -> Owner B)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400`
- Plan: `~/docs/plans/2026-02-26-owner-a-planb-seg400-smoke200-and-handoff.md`

## Summary

- A61/A62/A63 completed; Gate-S1 PASS.
- A64 smoke200 completed for both baseline and planb; Gate-S2 PASS.
- No new full600 run was executed (budget guard respected).

## Required reference paths (for report-pack v18 refresh)

- `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json`
- `outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200/`
- `outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/`
- `notes/anti_cherrypick_seg400_460.md`

## Gate outcomes

- Gate-S1:
  - `match_ratio_over_eligible = 0.5510`
  - clip threshold ratio vs canonical = `1.2492x`
  - verdict: PASS
- Gate-S2 (`test_step0199`):
  - baseline: PSNR `12.5889`, LPIPS `0.6277`, tLPIPS `0.08518`
  - planb: PSNR `12.7610`, LPIPS `0.5839`, tLPIPS `0.03527`
  - deltas (planb - baseline): `+0.1721 / -0.0438 / -0.0499`
  - verdict: PASS (condition 1 and 2 both satisfied)

## Notes for Owner B

- This segment adds anti-cherrypick evidence at later time window (`frame_start=400`) without consuming extra full600 budget.
- Evidence can be appended to the existing Plan-B defense narrative as a third slice confirming trend consistency.
