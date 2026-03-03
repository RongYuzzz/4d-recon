# Writing Mode v26 (Owner B, No-GPU) Implementation Plan: Meeting Index + Wire Looped Clips

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `N=0` 冻结期内（No‑GPU、无新增训练），把 v26 的会议材料入口进一步“收口成一个索引页”，并在 Owner A 产出 loop clip + 播放 runbook 后把引用接线到 handout/onepager。

**Architecture:** 以 `docs/decisions/2026-02-26-planb-v26-freeze.md` 为唯一决议真源；会中数字只引用 `docs/report_pack/2026-02-26-v26/` 四件套；所有新增内容仅为 `docs/`/`notes/` 的入口索引与引用接线，不引入新 report-pack 版本号，不新打 tarball。

**Tech Stack:** Markdown、ripgrep（`rg`）、Python unit tests（`scripts/tests/test_*.py`）、git worktree。

---

## 约束（必须遵守）

- 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`），不新增 smoke200/full600。
- 不改协议：不改 `docs/protocols/protocol_v1.yaml`；不改训练数值逻辑。
- 不入库大文件：`data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 会中数字口径：只允许引用 v26 report-pack 快照：
  - `docs/report_pack/2026-02-26-v26/metrics.csv`
  - `docs/report_pack/2026-02-26-v26/scoreboard.md`
  - `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
  - `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`

---

### Task 1: 建立隔离 worktree + 预检

**Files:**
- Create: `notes/owner_b_v26_meeting_index_preflight.md`
- Test: `scripts/tests/test_build_report_pack.py`
- Test: `scripts/tests/test_summarize_scoreboard.py`
- Test: `scripts/tests/test_summarize_planb_anticherrypick.py`

**Step 1: 创建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v26-meeting-index .worktrees/owner-b-20260226-writing-mode-v26-meeting-index origin/main
cd .worktrees/owner-b-20260226-writing-mode-v26-meeting-index
git status -sb
```

Expected: worktree 干净，分支基于 `origin/main`。

**Step 2: 运行最小回归**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: 全 PASS。

**Step 3: 写 preflight 记录**

Create `notes/owner_b_v26_meeting_index_preflight.md`，包含：
- 时间戳、分支名、HEAD、worktree 路径
- 3 项测试 PASS 记录

**Step 4: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
git add notes/owner_b_v26_meeting_index_preflight.md
git commit -m "docs(preflight): add v26 meeting-index preflight (no-gpu)"
```

---

### Task 2: 新增“会议入口索引页”（Start Here）

**Files:**
- Create: `docs/reviews/2026-02-26/meeting-index-v26.md`

**Step 1: 创建索引页**

Create `docs/reviews/2026-02-26/meeting-index-v26.md`，结构建议（每节 3–8 行，避免长篇）：

- `Start Here (2 min)`：先读 `docs/reviews/2026-02-26/meeting-handout-v26.md`
- `Presenter Pack`：
  - `docs/writing/planb_talk_outline_v26.md`
  - `docs/writing/planb_qa_cards_v26.md`
  - `notes/planb_meeting_assets_v26_owner_a.md`
  - （条件）`notes/planb_meeting_runbook_v26_owner_a.md`（若存在）
- `Evidence Source of Truth`：v26 report-pack 四件套 + v26 freeze 决议
- `Key Deltas`：一句话明确 `Δ = planb - baseline`，并注明 smoke200/full600 口径差异
- `No-New-Training Rule`：强调新增 full600 `N=0`、禁止新增训练

**Step 2: 自检（不允许 TODO/漂移）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
rg -n "TODO" docs/reviews/2026-02-26/meeting-index-v26.md || true
rg -n "N=0|新增 full600" docs/reviews/2026-02-26/meeting-index-v26.md
```

Expected:
- 不出现 `TODO`
- 出现 `N=0`（预算纪律）

**Step 3: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
git add docs/reviews/2026-02-26/meeting-index-v26.md
git commit -m "docs(review): add v26 meeting index (start here)"
```

---

### Task 3: 更新 docs 索引入口（减少“找不到最新材料”）

**Files:**
- Modify: `docs/README.md`

**Step 1: 更新 `docs/README.md`**

在合适位置新增一条入口（不改现有结构也可，最小增量）：
- `docs/reviews/2026-02-26/meeting-index-v26.md`
- `docs/reviews/2026-02-26/meeting-handout-v26.md`
- `docs/decisions/2026-02-26-planb-v26-freeze.md`

**Step 2: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
git add docs/README.md
git commit -m "docs(index): link v26 meeting index/handout and freeze decision"
```

---

### Task 4: 条件接线（Owner A 的 loop clip + runbook）

**Files:**
- Modify (conditional): `docs/reviews/2026-02-26/meeting-handout-v26.md`
- Modify (conditional): `docs/writing/planb_onepager_v26.md`
- Modify (conditional): `docs/writing/planb_talk_outline_v26.md`
- Modify (conditional): `docs/reviews/2026-02-26/meeting-index-v26.md`

**Step 1: 检查依赖是否到位**

依赖（若缺失则跳过 Task 4，不阻塞合入）：
- `notes/planb_meeting_runbook_v26_owner_a.md`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/`（非入库路径，仅作存在性检查）

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
test -f /root/projects/4d-recon/notes/planb_meeting_runbook_v26_owner_a.md && echo "runbook: OK" || echo "runbook: MISSING"
test -d /root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/clips_v26_looped && echo "looped clips dir: OK" || echo "looped clips dir: MISSING"
```

**Step 2: 最小接线**

若 runbook 存在：
- 在 `meeting-handout-v26.md` 与 `planb_onepager_v26.md` 的播放清单处新增 1 行链接：
  - `notes/planb_meeting_runbook_v26_owner_a.md`
- 在 `planb_talk_outline_v26.md` 的播放部分注明“优先播放 loop12s 版本（若存在）”
- 在 `meeting-index-v26.md` 的 Presenter Pack 中加 runbook 一行

**Step 3: Commit（若 Step 2 有改动）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
git add docs/reviews/2026-02-26/meeting-handout-v26.md docs/writing/planb_onepager_v26.md docs/writing/planb_talk_outline_v26.md docs/reviews/2026-02-26/meeting-index-v26.md
git commit -m "docs(writing): wire owner-a looped clips runbook into meeting docs"
```

---

### Task 5: 最终回归 + 推送合入

**Files:**
- (none)

**Step 1: 全量 tests**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: 全 PASS。

**Step 2: Rebase + Push**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-index
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected: 推送成功，主线不包含任何 `outputs/`/`data/`/`*.tar.gz` 变更。

