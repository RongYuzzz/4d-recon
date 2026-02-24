# T0 Gate Decision

- Timestamp: `2026-02-24T10:36:56+08:00`
- Dataset source: `fixture`
- Dataset path: `/root/projects/4d-recon/.worktrees/owner-c-20260224/data/gate1_fixture_adapted_v2`

## Artifacts
- Baseline CSV: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/baseline/t0_grad.csv`
- Zero-velocity CSV: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/zero_velocity/t0_grad.csv`
- Baseline MP4: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/baseline/videos/traj_4d_step199.mp4`
- Zero-velocity MP4: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/zero_velocity/videos/traj_4d_step199.mp4`

## Decision
- Baseline: `rows=200, finite=True, nonzero_v=200, nonzero_d=200`
- Zero-velocity: `rows=200, finite=True, nonzero_v=200, nonzero_d=200`
- Gate conclusion: `PASS`

## Notes
- SelfCap Gate-1 dataset (`data/selfcap_bar_8cam60f`) was not ready in this workspace.
- This run used the fixture fallback and should be rerun on real SelfCap data once available.
