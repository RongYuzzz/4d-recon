# Plan-B seg300_360 Preflight (Owner A)

- Date: 2026-02-26
- Worktree: `/root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300`
- HEAD: `323e5281c0cfa921c8fd7eae79bf142c0e8efd64`

## Recent 5 commits

1. `323e528` docs(plan): add owner-a planb seg300_360 smoke200 handoff plan
2. `46fa424` docs(planb): re-template seg400/seg1800 smoke200 to isolate velocity init
3. `f435af1` docs(report-pack): snapshot v25 with template-hygiene evidence
4. `b8ca428` docs(planb): add template-hygiene defense note for seg slices
5. `21f1ff6` docs(plan): add owner-b writing-mode v25 plan

## Preflight tests

- `python3 scripts/tests/test_init_velocity_from_points_contract.py`: PASS
- `python3 scripts/tests/test_pack_evidence.py`: PASS

## Runtime path note

- Worktree 内 `data/` 与 `outputs/` 为仓库占位目录（非主工作区共享 symlink）。
- 为保证产物在主阵地统一可见，本任务中的数据生成与训练结果路径使用主工作区绝对路径：`/root/projects/4d-recon/data` 与 `/root/projects/4d-recon/outputs`。
