# Writing Mode v26 (Owner B, No-GPU) Implementation Plan: Meeting Checklist + Optional Offline Bundle Wiring

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `N=0` 冻结期内（No‑GPU、无新增训练），补齐一份“会前 2 分钟 checklist”，并在 Owner A 产出离线 bundle 后，把入口最小接线到 meeting index/handout（不引入新 report-pack 版本号）。

**Architecture:** 以 `docs/decisions/2026-02-26-planb-v26-freeze.md` 为唯一决议真源；会中数字只引用 v26 report-pack 四件套；新增内容仅为 `docs/`/`notes/` 的检查清单与入口接线，避免任何指标口径漂移。

**Tech Stack:** Markdown、bash、`rg`、Python unit tests（`scripts/tests/test_*.py`）、git worktree。

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
- Create: `notes/owner_b_v26_meeting_checklist_preflight.md`
- Test: `scripts/tests/test_build_report_pack.py`
- Test: `scripts/tests/test_summarize_scoreboard.py`
- Test: `scripts/tests/test_summarize_planb_anticherrypick.py`

**Step 1: 创建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v26-meeting-checklist .worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist origin/main
cd .worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
git status -sb
```

Expected: worktree 干净，分支基于 `origin/main`。

**Step 2: 最小回归**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: 全 PASS。

**Step 3: 写 preflight 记录**

Create `notes/owner_b_v26_meeting_checklist_preflight.md`，包含：
- 时间戳、分支名、HEAD、worktree 路径
- 3 项测试 PASS

**Step 4: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
git add notes/owner_b_v26_meeting_checklist_preflight.md
git commit -m "docs(preflight): add v26 meeting-checklist preflight (no-gpu)"
```

---

### Task 2: 新增会前 Checklist（2 分钟版）

**Files:**
- Create: `docs/reviews/2026-02-26/meeting-checklist-v26.md`

**Step 1: 编写 checklist**

Create `docs/reviews/2026-02-26/meeting-checklist-v26.md`，必须包含以下段落（每段 3–8 行）：

1. **入口**：`meeting-index-v26.md` / `meeting-handout-v26.md`（点击顺序）
2. **冻结纪律**：`N=0`、禁止新增训练（并指向 freeze 决议）
3. **数字真源**：v26 report-pack 四件套存在性检查命令
4. **evidence tar SHA**：v26 tar 的 `rg` + `sha256sum` 校验命令
5. **视频资产自检**：loop12s 优先，runbook 自检命令（指向 `notes/planb_meeting_runbook_v26_owner_a.md`）
6. **兜底**：covers freeze-frame 与 raw mp4 fallback（只写路径/原则，不重复 runbook 全文）
7. **禁止项**：明确“不要现场跑实验/不要生成新 report-pack vXX”

**Step 2: 自检（不得含 TODO）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
rg -n "TODO" docs/reviews/2026-02-26/meeting-checklist-v26.md || true
rg -n "N=0|新增 full600" docs/reviews/2026-02-26/meeting-checklist-v26.md
```

Expected:
- 不出现 `TODO`
- 出现 `N=0`

**Step 3: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
git add docs/reviews/2026-02-26/meeting-checklist-v26.md
git commit -m "docs(review): add v26 pre-meeting checklist (2-minute)"
```

---

### Task 3: 更新 meeting index（加 checklist 入口）

**Files:**
- Modify: `docs/reviews/2026-02-26/meeting-index-v26.md`

**Step 1: 最小增量接线**

在 `Start Here` 或单独新增一行，把 checklist 加入入口（不改变原结构也可）。

**Step 2: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
git add docs/reviews/2026-02-26/meeting-index-v26.md
git commit -m "docs(review): link v26 meeting checklist from index"
```

---

### Task 4: 条件接线（Owner A 离线 bundle）

**Files:**
- Modify (conditional): `docs/reviews/2026-02-26/meeting-index-v26.md`
- Modify (conditional): `docs/reviews/2026-02-26/meeting-handout-v26.md`
- Modify (conditional): `docs/reviews/2026-02-26/meeting-checklist-v26.md`

**Step 1: 检查离线 bundle 是否到位**

依赖（不入库文件，仅作存在性检查）：
- `artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

Run:
```bash
test -f /root/projects/4d-recon/artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz && echo "offline bundle: OK" || echo "offline bundle: MISSING"
```

**Step 2: 若存在则最小接线**

若存在：
- 在 `meeting-index-v26.md` 增加 1 行：离线 bundle 路径 + “SHA 见 `notes/planb_meeting_assets_v26_owner_a.md`”。
- 在 `meeting-handout-v26.md` 的证据入口或播放清单处增加 1 行同样提示。
- 在 checklist 增加 1 个可选检查项：`sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`（并指向 notes 真源记录）。

**Step 3: Commit（仅当 Step 2 有改动）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
git add docs/reviews/2026-02-26/meeting-index-v26.md docs/reviews/2026-02-26/meeting-handout-v26.md docs/reviews/2026-02-26/meeting-checklist-v26.md
git commit -m "docs(review): wire optional offline meeting bundle into v26 docs"
```

---

### Task 5: 最终回归 + 推送合入

**Files:**
- (none)

**Step 1: 全量 tests**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: 全 PASS。

**Step 2: Rebase + Push**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting-checklist
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected: push 成功，且提交不包含 `outputs/`/`data/`/`*.tar.gz`。

