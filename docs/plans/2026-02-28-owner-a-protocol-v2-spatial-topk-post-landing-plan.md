# protocol_v2 Spatial Top-K Snapshots Post-Landing Follow-ups (Owner A) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Owner A 侧收口 `spatial metrics top-k frame snapshots` 落地后的维护动作：固化 GitHub(HTTPS) 连通性 gate，补最小使用说明（可选），并在 PR 合并后做工作区清理，避免后续再被 “443 timeout / fallback” 阻塞。

**Architecture:** 仅做 docs/ops 级别的小步改动（不触碰训练/预算/证据链）。所有任务尽量与 Owner B 并行；只有清理动作依赖 PR 合并。

**Tech Stack:** `git`(https)、`gh`、`pytest`。

---

## Parallelism Notes

- 可立即并行执行（不依赖 B）：Task A0、Task A1
- 依赖 B/PR 状态：Task A2（PR#1 合并后）

---

## Current State (2026-02-28)

- A 交付分支：`owner-a/protocol-v2-spatial-metrics-topk-frames-code`
  - commit: `37d32266b37fdd9b29a538c7002709e9b5c25d60`
- 既往阻塞：`git fetch/ls-remote` 访问 `github.com:443` 偶发 `SSL connection timeout`
  - 现状：PAT(classic) + `gh auth setup-git` 已配置完成（仍需把连通性 gate 固化为“每次交付前必跑”）

---

### Task A0: GitHub Connectivity Gate (Must, 2-5 min)

**Files:** none

**Step 1: 确认 gh 登录状态**

Run:
```bash
gh auth status -h github.com
```

Expected: 显示已登录账号；并提示 git operations 已配置。

**Step 2: 验证 git HTTPS 能在 20s 内访问 GitHub**

Run:
```bash
timeout 20s git ls-remote https://github.com/RongYuzzz/4d-recon.git HEAD
```

Expected: 打印 1 行 `<sha>\tHEAD`，且 exit code 为 0。

**Step 3: 验证 A 分支在远端可见**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
timeout 30s git ls-remote --heads origin owner-a/protocol-v2-spatial-metrics-topk-frames-code
```

Expected: 1 行 `refs/heads/owner-a/protocol-v2-spatial-metrics-topk-frames-code`，sha= `37d32266b37fdd9b29a538c7002709e9b5c25d60`。

**Step 4: 若仍失败（兜底，必须记录证据）**

Run:
```bash
gh api repos/RongYuzzz/4d-recon/branches/owner-a%2Fprotocol-v2-spatial-metrics-topk-frames-code --jq .commit.sha
GIT_TRACE_CURL=1 GIT_CURL_VERBOSE=1 timeout 20s \
  git ls-remote https://github.com/RongYuzzz/4d-recon.git HEAD
```

Expected: API 能返回 sha；并把失败日志保存到 PR comment 或单独 note（避免“口头修复”）。

---

### Task A1: Add Minimal “How To Run” to the Note (Recommended, 5-10 min)

**Files:**
- Modify: `notes/protocol_v2_spatial_metrics_topk_frames.md`

**Step 1: 在 note 末尾追加一个最小可复现命令段**

Append:
````markdown
## How to run

Example:
```bash
python3 scripts/viz_spatial_metrics_topk_frames.py \
  --renders_dir_a outputs/protocol_v2/selfcap_bar_8cam60f/planb_init_600/renders_test_step599 \
  --renders_dir_b outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600/renders_test_step599 \
  --delta_csv outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv \
  --out_dir outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599 \
  --k 10 --resize_w 960 --quality 85
```

Expected:
- writes `frame_*.jpg` + `README.md` under `--out_dir`.
````

**Step 2: 复跑 contract 测试**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-land-spatial-metrics-topk-code
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
```

Expected: `1 passed`。

**Step 3: 提交并推送到 A 分支（供 B 可选同步）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-land-spatial-metrics-topk-code
git add notes/protocol_v2_spatial_metrics_topk_frames.md
git commit -m "docs(protocol_v2): add how-to-run for spatial top-k snapshots"
git push
```

Expected: push 成功；B 如需同步可在其分支 `cherry-pick` 该 doc commit。

---

### Task A2: Cleanup A Worktree/Branch After PR Merge (Recommended, 2-5 min)

**Files:** none (repo hygiene)

**Step 1: 确认 PR#1 已合并**

Run:
```bash
gh pr view 1 --repo RongYuzzz/4d-recon --json number,state,headRefName,url
```

Expected: `state` 为 `MERGED`（或按团队流程 `CLOSED`）。

**Step 2: 移除本地 A worktree（只在 clean 时执行）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git -C .worktrees/owner-a-land-spatial-metrics-topk-code status -sb
git worktree remove .worktrees/owner-a-land-spatial-metrics-topk-code
```

Expected: worktree 移除成功。

**Step 3: 删除 A 的远端分支（可选，按策略）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git push origin --delete owner-a/protocol-v2-spatial-metrics-topk-frames-code
```

Expected: 远端分支删除成功；若团队要求保留审计分支，则跳过本步骤。

