# Feature-Loss v2 Post-Fix 预检记录（Owner A）

- 时间：`2026-02-25T23:37:59+08:00`
- 分支：`owner-a-20260226-v2-postfix`
- worktree：`/root/projects/4d-recon/.worktrees/owner-a-20260226-v2-postfix`
- 执行 HEAD：`e761b18296f1f1b71dcf0b4e0c55e69f664c6a38`

## 1) Git provenance（最近 3 条）

```text
e761b18 docs(plans): add owner-b v2 no-gpu diagnostics and efficiency tooling plan
8b4826f docs(plans): add owner-a v2 post-fix rerun and decision plan
14b4762 docs+notes: integrate A v2 rerun evidence (v14) and B v2 status
```

补充校验：当前历史中已包含：
- `d1b95b2 fix(vggt): align token_proj phi render with cache downscale via bilinear resize`
- `a859078 docs+scripts: make v2 M1 defaults more conservative and require baseline_smoke200 comparison`

## 2) 快速健康检查（无 GPU）

- `python3 scripts/tests/test_token_proj_resize_alignment.py` -> PASS
- `python3 scripts/tests/test_feature_loss_v2_artifacts_exist.py` -> PASS
- `python3 scripts/tests/test_vggt_cache_contract.py` -> PASS

## 3) 数据契约检查

- 新 worktree 下创建链接：
  - `data/selfcap_bar_8cam60f -> /root/projects/4d-recon/data/selfcap_bar_8cam60f`
- 目录检查通过：
  - `data/selfcap_bar_8cam60f/images`
  - `data/selfcap_bar_8cam60f/triangulation`
  - `data/selfcap_bar_8cam60f/sparse/0`

## 4) 结论

Task 1 通过，进入 Task 2（M1 smoke200 + 最小 lambda sweep）。
