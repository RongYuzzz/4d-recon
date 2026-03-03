# v26 Offline Bundle SHA Source-of-Truth Fix (Owner A) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 v26 offline meeting bundle 的 SHA “真源”不一致问题，避免按文档校验时误报，同时保持 bundle 仍为 local-only（不入库）。

**Architecture:** 将 offline bundle 的 SHA256 维护为单一真源（建议以 `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md` 为准），并确保所有对外入口引用到一致口径；bundle 本体继续由 `.gitignore` 忽略，绝不进入 git。

**Tech Stack:** git + bash（`sha256sum`/`rg`/`git check-ignore`）+ 现有脚本测试（`scripts/tests/test_*.py`）。

---

### Task 1: Preflight (Freeze Discipline + Local Artifact Hygiene)

**Files:**
- Modify: (none)

**Step 1: Sync and confirm clean state**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git rebase origin/main
git status --porcelain=v1
```

Expected:
- `git status` 输出为空（或仅包含你本地无关的未跟踪文件；本任务不新增/不提交 `artifacts/**/*.tar.gz`）。

**Step 2: Confirm bundle is ignored (must not be tracked)**

Run:
```bash
cd /root/projects/4d-recon
git ls-files artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz || true
git check-ignore -v artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz
```

Expected:
- `git ls-files ...` 无输出
- `git check-ignore -v ...` 命中 `.gitignore` 中的 `artifacts/meeting_assets/*.tar.gz`

**Step 3: Compute current SHA256 (ground truth)**

Run:
```bash
cd /root/projects/4d-recon
sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz
```

Expected:
- 输出为 `dee936ac9bef7cb88264de9641d3d2d04b4036ee2a76d66a932e7176b84e7dc3  artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

---

### Task 2: Fix SHA Source-of-Truth in Asset Note

**Files:**
- Modify: `notes/planb_meeting_assets_v26_owner_a.md`

**Step 1: Edit offline bundle section to avoid stale SHA**

Change the offline bundle subsection to:
- 要么直接把 SHA 更新为当前值 `dee936...`
- 要么更稳健：把“SHA 真源”改为引用自检记录 `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`，并注明“以 selfcheck 为准”

Recommended patch intent (preferred):
- 在 `## 7) Offline bundle (local only, non-git artifact)` 中，将原先硬编码 SHA 行替换为：
  - `- SHA256 (source of truth): \`notes/meeting_offline_bundle_v26_selfcheck_owner_a.md\``
  - 可选：在下一行保留当前 SHA 作为冗余显示，但明确“若重打包，以 selfcheck 为准”

**Step 2: Verify old SHA no longer appears**

Run:
```bash
cd /root/projects/4d-recon
rg -n "89a17a3ad9987e006385aaaee3c25fa00f6e5c4fe3ff53491d7bb705957826e4" -S notes/planb_meeting_assets_v26_owner_a.md
```

Expected:
- 无匹配输出

---

### Task 3: Align Selfcheck Note Wording (No Contradictions)

**Files:**
- Modify: `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`

**Step 1: Update the explanatory note so it remains true after Task 2**

Currently it says the checksum differs from the earlier asset note. After Task 2, update that sentence to something that remains correct, e.g.:
- “This hygiene pass rebuilt the local tar to include `meeting-checklist-v26.md`; SHA below is the current ground truth.”

**Step 2: Confirm selfcheck SHA matches actual file**

Run:
```bash
cd /root/projects/4d-recon
sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz
rg -n "SHA256:" -n notes/meeting_offline_bundle_v26_selfcheck_owner_a.md
```

Expected:
- `sha256sum` 与 selfcheck note 中记录一致（`dee936...`）

---

### Task 4: Repo-Wide Sanity (No Stale SHA in Meeting Entrypoints)

**Files:**
- Modify: (none) unless you find stale hard-coded SHA elsewhere

**Step 1: Search for old/new SHA in docs**

Run:
```bash
cd /root/projects/4d-recon
rg -n "89a17a3a|dee936ac|planb_meeting_assets_v26\\.tar\\.gz" -S docs/reviews/2026-02-26 docs/writing notes
```

Expected:
- meeting docs 不硬编码某个 SHA，仅引用“SHA 真源”文件路径
- 若仍有硬编码旧 SHA，优先在 notes 侧修复，避免改动 meeting docs（减少与 Owner B 冲突）

---

### Task 5: Tests (No-GPU)

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

### Task 6: Commit + Push (Small, Docs-Only)

**Files:**
- Modify: `notes/planb_meeting_assets_v26_owner_a.md`
- Modify: `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`

**Step 1: Commit**

Run:
```bash
cd /root/projects/4d-recon
git add notes/planb_meeting_assets_v26_owner_a.md notes/meeting_offline_bundle_v26_selfcheck_owner_a.md
git commit -m "docs(meeting): fix v26 offline bundle sha source-of-truth"
```

Expected:
- 提交只包含上述两个 notes 文件（不包含 `artifacts/meeting_assets/*.tar.gz`）

**Step 2: Push**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected:
- push 成功

