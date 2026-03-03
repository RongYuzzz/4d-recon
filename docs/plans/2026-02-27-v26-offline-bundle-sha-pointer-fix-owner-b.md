# v26 Offline Bundle SHA Pointer Fix (Owner B) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 v26 meeting/writing 文档中 “offline bundle 的 SHA 真源” 统一指向 `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`，避免当前指向 `notes/planb_meeting_assets_v26_owner_a.md` 造成的 SHA 不一致误报；保持 offline bundle 仍为 local-only（不入库）。

**Architecture:** meeting docs 不硬编码 SHA；只给出校验命令与 “SHA 真源” 的单一指向（selfcheck note）。资产清单 note 仍作为“包含哪些文件/如何使用”入口，selfcheck note 作为“当前 bundle SHA/迁移完整性”入口。

**Tech Stack:** Markdown docs + `rg` + git + Python tests（No-GPU）。

---

### Task 1: Preflight (No-GPU + Freeze Discipline)

**Files:**
- Modify: (none)

**Step 1: Sync to latest `origin/main`**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git rebase origin/main
git status --porcelain=v1
```

Expected:
- 工作区干净（或仅有你本地无关未跟踪文件；本任务只改 `docs/`、`notes/`）。

**Step 2: Confirm selfcheck note exists**

Run:
```bash
cd /root/projects/4d-recon
test -f notes/meeting_offline_bundle_v26_selfcheck_owner_a.md && echo OK
```

Expected:
- 输出 `OK`

---

### Task 2: Update Offline Bundle “SHA 真源” Pointer in Meeting Docs

**Files:**
- Modify: `docs/reviews/2026-02-26/meeting-index-v26.md`
- Modify: `docs/reviews/2026-02-26/meeting-handout-v26.md`
- Modify: `docs/reviews/2026-02-26/meeting-checklist-v26.md`
- Modify: `docs/writing/planb_onepager_v26.md`

**Step 1: Replace “SHA 真源” target**

Edit the offline bundle lines so that:
- `SHA 真源：` points to `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`
- Keep the bundle path and verification command unchanged:
  - `artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`
  - `sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

Examples (intent):
- Before: `SHA 真源：notes/planb_meeting_assets_v26_owner_a.md`
- After:  `SHA 真源：notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`

**Step 2: Verify no remaining references to the old SHA pointer**

Run:
```bash
cd /root/projects/4d-recon
rg -n "SHA 真源：`notes/planb_meeting_assets_v26_owner_a\\.md`|SHA 真源：`notes/meeting_offline_bundle_v26_selfcheck_owner_a\\.md`" -S \
  docs/reviews/2026-02-26/meeting-index-v26.md \
  docs/reviews/2026-02-26/meeting-handout-v26.md \
  docs/reviews/2026-02-26/meeting-checklist-v26.md \
  docs/writing/planb_onepager_v26.md
```

Expected:
- 仅出现新指向 `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`

---

### Task 3: Sanity Checks (No Absolute Paths, No TODO, No SHA Hardcode)

**Files:**
- Modify: (none) unless checks fail

**Step 1: Ensure meeting docs don’t contain `/root/projects/4d-recon`**

Run:
```bash
cd /root/projects/4d-recon
rg -n "/root/projects/4d-recon" -S docs/reviews/2026-02-26 docs/writing/planb_*_v26.md notes/planb_meeting_runbook_v26_owner_a.md || true
```

Expected:
- 无输出（或仅允许出现在明确标注“主阵地”的历史 runbook 文档里；meeting v26 入口文件应避免绝对路径）

**Step 2: Ensure no TODO in v26 meeting docs**

Run:
```bash
cd /root/projects/4d-recon
rg -n "\\bTODO\\b" -S docs/reviews/2026-02-26 docs/writing/planb_*_v26.md || true
```

Expected:
- 无输出

**Step 3: Ensure meeting docs don’t hardcode the bundle SHA**

Run:
```bash
cd /root/projects/4d-recon
rg -n "dee936ac9bef7cb88264de9641d3d2d04b4036ee2a76d66a932e7176b84e7dc3" -S \
  docs/reviews/2026-02-26 docs/writing/planb_*_v26.md || true
```

Expected:
- 无输出（SHA 仅在 selfcheck note 中维护；meeting docs 只指向真源）

---

### Task 4: Tests (No-GPU)

**Files:**
- Test: `scripts/tests/test_pack_evidence.py`
- Test: `scripts/tests/test_build_report_pack.py`
- Test: `scripts/tests/test_summarize_scoreboard.py`
- Test: `scripts/tests/test_summarize_planb_anticherrypick.py`

**Step 1: Run tests**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected:
- 全 PASS

---

### Task 5: Commit + Push (Docs-Only)

**Files:**
- Modify: `docs/reviews/2026-02-26/meeting-index-v26.md`
- Modify: `docs/reviews/2026-02-26/meeting-handout-v26.md`
- Modify: `docs/reviews/2026-02-26/meeting-checklist-v26.md`
- Modify: `docs/writing/planb_onepager_v26.md`

**Step 1: Commit**

Run:
```bash
cd /root/projects/4d-recon
git add \
  docs/reviews/2026-02-26/meeting-index-v26.md \
  docs/reviews/2026-02-26/meeting-handout-v26.md \
  docs/reviews/2026-02-26/meeting-checklist-v26.md \
  docs/writing/planb_onepager_v26.md
git commit -m "docs(meeting): point offline bundle sha source to selfcheck note"
```

Expected:
- 提交仅包含上述 `docs/*` 文件（不包含任何 `artifacts/**/*.tar.gz`）

**Step 2: Rebase + Push**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected:
- push 成功

