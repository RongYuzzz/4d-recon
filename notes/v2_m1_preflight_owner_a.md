# Feature-Loss v2 M1 预检记录（Owner A）

- 时间：2026-02-25T22:14:25+08:00
- 执行分支：`owner-a-20260225-v2-rerun`
- 执行工作树：`/root/projects/4d-recon/.worktrees/owner-a-20260225-v2-rerun`
- 训练基线提交：`2948fa0`（当次执行时的 `origin/main`）

## 1) 隔离环境

- 保留旧冲突 worktree（`owner-a-20260225-v2-gpu-exec`）仅作 shim 历史记录，不继续运行。
- 新建干净 worktree（`owner-a-20260225-v2-rerun`）并在其内执行 M1/M2。

## 2) 数据契约检查

- 数据路径：`data/selfcap_bar_8cam60f`
- 本地链接：`data/selfcap_bar_8cam60f -> /root/projects/4d-recon/data/selfcap_bar_8cam60f`
- canonical 结构可用（`images/`、`triangulation/`、`sparse/0`）。

## 3) 代码/脚本可用性短检

- `python3 scripts/tests/test_feature_loss_v2_artifacts_exist.py`：PASS
- `python3 scripts/tests/test_vggt_preprocess_consistency_dummy.py`：PASS
- `python3 scripts/tests/test_summarize_scoreboard.py`：PASS
- `scripts/check_vggt_preprocess_consistency.py`（backend=vggt, depth, 6帧）：PASS

## 4) Gate M1 准备结论

- M1 运行前置条件满足，可进入 200-step 三条对齐实验（baseline_smoke200 / v2_smoke200 / v2_gated_smoke200）。
