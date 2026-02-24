# T0 Gate Decision

- Timestamp: `2026-02-24T11:06:16+08:00`
- Dataset source: `real selfcap`
- Dataset path: `/root/projects/4d-recon/data/selfcap_bar_8cam60f`

## Artifacts
- As-run paths (historical, may not persist if worktree is removed):
  - Baseline CSV: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/baseline/t0_grad.csv`
  - Zero-velocity CSV: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/zero_velocity/t0_grad.csv`
  - Baseline MP4: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/baseline/videos/traj_4d_step199.mp4`
  - Zero-velocity MP4: `/root/projects/4d-recon/.worktrees/owner-c-20260224/outputs/t0_selfcap/zero_velocity/videos/traj_4d_step199.mp4`

- Canonical paths (recommended on rerun from main workspace):
  - Baseline CSV: `outputs/t0_selfcap/baseline/t0_grad.csv`
  - Zero-velocity CSV: `outputs/t0_selfcap/zero_velocity/t0_grad.csv`
  - Baseline MP4: `outputs/t0_selfcap/baseline/videos/traj_4d_step199.mp4`
  - Zero-velocity MP4: `outputs/t0_selfcap/zero_velocity/videos/traj_4d_step199.mp4`
  - Repro: `notes/demo-runbook.md` Step 3

## Decision
- Baseline: `rows=200, finite=True, nonzero_v=200, nonzero_d=200`
- Zero-velocity: `rows=200, finite=True, nonzero_v=200, nonzero_d=200`
- Gate conclusion: `PASS`

## Notes
- This run supersedes the earlier fixture fallback result.
- Main workspace currently exposes `data/selfcap_bar_8cam60f` (symlinked dataset), and this audit is based on that real dataset path.
