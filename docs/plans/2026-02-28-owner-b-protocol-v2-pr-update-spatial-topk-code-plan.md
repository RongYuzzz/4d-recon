# protocol_v2 PR Update: Add Spatial Metrics Top-K Snapshots Code + Pointers Implementation Plan (Owner B / GPU1)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Owner A 的 “spatial metrics top‑k frame snapshots” 代码与说明（脚本+单测+note）合入 `owner-b/protocol-v2-land-v2-pack` 并更新 report-pack README 入口，再重打离线包与回填 manifest，确保 PR（#1）证据链完整且 `manifest_match: yes`。

**Architecture:** 在 `.worktrees/owner-b-land-v2-pack` 上操作：先 cherry-pick A 的提交；再在 `docs/report_pack/2026-02-27-v2/README.md` 增补指针；最后按固定顺序闭环（`pack_evidence` → 解出 tar 内 manifest 覆盖 docs 快照 → `manifest_match` 校验 → push → PR 自动更新）。

**Tech Stack:** `git`、`pytest`、`python3`、`tar`、`rg`。（GPU1 不强依赖。）

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；本计划只做 PR 收口与证据链闭环。
- `docs/report_pack/2026-02-27-v2/README.md` 或 `notes/*.md` 的任何变更都会影响 tar/manifest，必须重打 tar 并回填 manifest 快照。
- `manifest_match: yes` 是 release gate。

---

### Task 0: Preflight（5 分钟）

**Step 1: 进入 worktree 并确认分支干净**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
git status -sb --porcelain
git rev-parse --abbrev-ref HEAD
```
Expected: 分支为 `owner-b/protocol-v2-land-v2-pack` 且 clean。

**Step 2: 确认当前 PR 仍然打开且 head 正确（可选）**

Run:
```bash
gh pr view 1 --json number,state,baseRefName,headRefName,url
```
Expected: `state=OPEN`，`baseRefName=main`，`headRefName=owner-b/protocol-v2-land-v2-pack`。

---

### Task 1: 合入 A 的提交（10 分钟）

**依赖**：A 已推送分支 `owner-a/protocol-v2-spatial-metrics-topk-frames-code`（或提供 bundle/patch）。

**Option A（推荐）：从远端分支 cherry-pick**

Run:
```bash
git fetch origin owner-a/protocol-v2-spatial-metrics-topk-frames-code
git log --oneline --decorate --max-count=5 FETCH_HEAD
git cherry-pick FETCH_HEAD
```

**Option B（兜底）：若 A 提供 patches**

Run:
```bash
git am /path/to/patches_owner-a_spatial-metrics-topk-frames-code/*.patch
```

**Acceptance:**
- 3 个文件在本分支出现：
  - `scripts/viz_spatial_metrics_topk_frames.py`
  - `scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py`
  - `notes/protocol_v2_spatial_metrics_topk_frames.md`

---

### Task 2: 更新 report-pack README 入口（5-10 分钟）

**Files:**
- Modify: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: 在 “spatial metrics（per-frame GT vs Pred）” 小节追加 top‑k 快照指针**

最小新增三条即可：
- `notes/protocol_v2_spatial_metrics_topk_frames.md`
- `outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/README.md`
- 一句话：top‑k 快照集中 `52-59`（另含 `0`），解释 MAE 局部劣化并与 `41->42` 时序锚点互补

**Step 2: commit**

Run:
```bash
git add docs/report_pack/2026-02-27-v2/README.md
git commit -m "docs(report_pack): add spatial metrics top-k frame snapshot pointers"
```

---

### Task 3: 测试（5 分钟）

Run:
```bash
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
pytest -q scripts/tests/test_pack_evidence.py \
  scripts/tests/test_pack_evidence_follows_outputs_symlinks.py \
  scripts/tests/test_pack_evidence_protocol_v2_sources.py \
  scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py
```
Expected: 全部 PASS。

---

### Task 4: 重打离线包 + 回填 manifest（10-20 分钟）

**Step 1: 重打 tar**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
```

**Step 2: 用 tar 内 manifest 覆盖回填快照并 commit**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
git add docs/report_pack/2026-02-27-v2/manifest_sha256.csv
git commit -m "docs(report_pack): refresh manifest snapshot from offline tar"
```

**Step 3: 校验 manifest_match**

Run:
```bash
tmp=$(mktemp)
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > "$tmp"
cmp -s "$tmp" docs/report_pack/2026-02-27-v2/manifest_sha256.csv && echo "manifest_match: yes" || echo "manifest_match: no"
rm -f "$tmp"
```
Expected: `manifest_match: yes`。

---

### Task 5: push + 更新 PR（5-10 分钟）

Run:
```bash
git push
gh pr view 1 --json number,state,url,headRefName
```
Expected: push 成功；PR head 仍为该分支，自动包含新提交。

---

### Task 6: PR comment（可选，2 分钟）

在 PR 里补一条 comment（或更新描述）说明：
- 已加入 spatial metrics top‑k 快照入口（`outputs/report_pack/diagnostics/spatial_metrics_topk_frames_...`）
- `manifest_match: yes`，离线包已重打

