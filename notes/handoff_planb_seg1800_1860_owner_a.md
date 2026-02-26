# Handoff: Plan-B seg1800_1860 smoke200 (Owner A -> Owner B)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800`
- Plan: `~/docs/plans/2026-02-26-owner-a-planb-seg1800_1860-smoke200-and-handoff.md`

## Summary

- A101/A102/A103 completed; Gate-S1 PASS.
- A104 smoke200 completed for both baseline and planb; Gate-S2 PASS.
- A105 side-by-side video generated locally (not committed).
- No new full600 run was executed (budget guard respected).

## Required reference paths (for report-pack/writeup refresh)

- `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json`
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/`
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/`
- `notes/anti_cherrypick_seg1800_1860.md`

## Gate outcomes

- Gate-S1:
  - `match_ratio_over_eligible = 0.5360`
  - clip threshold ratio vs canonical = `1.5715x`
  - verdict: PASS
- Gate-S2 (`test_step0199`):
  - baseline: PSNR `12.5796`, LPIPS `0.6290`, tLPIPS `0.08884`
  - planb: PSNR `12.7081`, LPIPS `0.5845`, tLPIPS `0.03557`
  - deltas (planb - baseline): `+0.1285 / -0.0445 / -0.0533`
  - verdict: PASS (condition 1 and 2 both satisfied)

## Notes for Owner B

- This segment adds a farther anti-cherrypick slice (`frame_start=1800`) without consuming full600 budget.
- Trend remains aligned with previous slices and can be appended directly to Plan-B defense narrative.
- Optional qualitative video: `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4`.
