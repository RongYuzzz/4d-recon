# protocol_v2 Land Spatial Metrics Top-K Snapshots Code to Git Implementation Plan (Owner A / GPU0)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 A 已完成但尚未提交的 “spatial metrics top‑k frame snapshots” 代码与说明（脚本+单测+note）整理成**干净的 git 提交**并推送到远端分支，供 Owner B 直接 cherry-pick 进 PR，避免仅有离线包产物而缺少可追溯源码/说明。

**Architecture:** 在基于 `origin/main` 的独立 worktree 中，仅复制 3 个文件（脚本、测试、note），跑单测确认可重复，再提交为 1~2 个 commit；若 `git push` 受网络影响，则生成 `git bundle` 或 `format-patch` 作为离线交付给 B。

**Tech Stack:** `git`、`pytest`、`python3`。（本任务不需要 GPU；若跑任何 GPU 相关可选项，必须显式 `CUDA_VISIBLE_DEVICES=0`。）

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；不改动 stage‑1/v26 证据链。
- 提交中**不得**包含 `outputs/`（gitignore 的大文件目录），只提交脚本/测试/文档。
- 目标是让 B 能 `git cherry-pick` 并且 `pytest` 可复跑。

---

### Task 0: Preflight（5 分钟）

**Files:**
- Read: `scripts/viz_spatial_metrics_topk_frames.py`
- Read: `scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py`
- Read: `notes/protocol_v2_spatial_metrics_topk_frames.md`

**Step 1: 确认 3 个文件在主工作区存在**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
ls -la scripts/viz_spatial_metrics_topk_frames.py \
  scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py \
  notes/protocol_v2_spatial_metrics_topk_frames.md
```
Expected: 3 个文件都存在。

---

### Task 1: 创建干净 worktree（5 分钟）

**Step 1: 基于 `origin/main` 创建 worktree**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-land-spatial-metrics-topk-code \
  -b owner-a/protocol-v2-spatial-metrics-topk-frames-code \
  origin/main
cd .worktrees/owner-a-land-spatial-metrics-topk-code
git status --porcelain
```
Expected: worktree clean。

---

### Task 2: 复制文件并跑单测（10-15 分钟）

**Step 1: 复制 3 个文件到 worktree**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-land-spatial-metrics-topk-code
cp -v ../../scripts/viz_spatial_metrics_topk_frames.py scripts/
cp -v ../../scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py scripts/tests/
cp -v ../../notes/protocol_v2_spatial_metrics_topk_frames.md notes/
```

**Step 2: 跑单测确认可重复**

Run:
```bash
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
```
Expected: `1 passed`。

---

### Task 3: 提交（5-10 分钟）

**Step 1: 提交为一个 commit（推荐）**

Run:
```bash
git add scripts/viz_spatial_metrics_topk_frames.py \
  scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py \
  notes/protocol_v2_spatial_metrics_topk_frames.md
git commit -m "feat(diagnostics): add spatial metrics top-k frame snapshot exporter"
```

Acceptance:
- `git show --name-only --pretty='' HEAD` 只包含上述 3 个文件。

---

### Task 4: 推送远端（含失败兜底）（5-15 分钟）

**Step 1: 正常 push**

Run:
```bash
git push -u origin owner-a/protocol-v2-spatial-metrics-topk-frames-code
```

**Step 2（兜底）：若 push 失败，生成离线交付物**

Run:
```bash
# bundle（可离线传输给 B 再 git fetch/pull）
git bundle create outputs/owner-a_spatial-metrics-topk-frames-code.bundle origin/main..HEAD

# format-patch（可离线发送给 B 再 git am）
mkdir -p outputs/patches_owner-a_spatial-metrics-topk-frames-code
git format-patch -o outputs/patches_owner-a_spatial-metrics-topk-frames-code origin/main..HEAD
```

---

### Task 5: 交接给 Owner B（2 分钟）

把以下信息发给 B（3 行即可）：
- 分支名：`owner-a/protocol-v2-spatial-metrics-topk-frames-code`
- commit hash：`git rev-parse HEAD`
-（若无法 push）bundle 路径或 patches 目录路径

