# Writing Mode v26 (Owner B, No-GPU) Implementation Plan: Wire Offline Bundle Into Meeting Docs

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `N=0` 冻结期内（No‑GPU、无新增训练），把 “离线会议 bundle（local tar）” 的入口与自检命令最小接线到 meeting docs（index/handout/checklist/onepager），并更新 docs 总索引，确保会前资料可以“一页跳全”。

**Architecture:** 以 `docs/decisions/2026-02-26-planb-v26-freeze.md` 为唯一决议真源；所有数值只引用 `docs/report_pack/2026-02-26-v26/` 四件套；离线 bundle 作为 **local-only 非入库物料**，只在文档中标注路径与校验方式，不把 tar 加入 git，不生成新 report-pack vXX。

**Tech Stack:** Markdown、bash、`rg`、Python unit tests（`scripts/tests/test_*.py`）、git worktree。

---

## 约束（必须遵守）

- 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`），不新增 smoke200/full600。
- 不改协议：不改 `docs/protocols/protocol_v1.yaml`；不改训练数值逻辑。
- 不入库大文件：`data/`、`outputs/`、`artifacts/**/*.tar.gz` 不入库（本计划只改 docs/notes）。
- 会中数字口径：只允许引用 v26 report-pack 快照：
  - `docs/report_pack/2026-02-26-v26/metrics.csv`
  - `docs/report_pack/2026-02-26-v26/scoreboard.md`
  - `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
  - `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`

---

### Task 1: 建立隔离 worktree + 预检

**Files:**
- Create: `notes/owner_b_v26_offline_bundle_wire_preflight.md`
- Test: `scripts/tests/test_build_report_pack.py`
- Test: `scripts/tests/test_summarize_scoreboard.py`
- Test: `scripts/tests/test_summarize_planb_anticherrypick.py`

**Step 1: 创建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v26-offline-wire .worktrees/owner-b-20260226-writing-mode-v26-offline-wire origin/main
cd .worktrees/owner-b-20260226-writing-mode-v26-offline-wire
git status -sb
```

Expected: worktree 干净。

**Step 2: 最小回归**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-offline-wire
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: 全 PASS。

**Step 3: 写 preflight 记录并提交**

Create `notes/owner_b_v26_offline_bundle_wire_preflight.md`（时间戳/分支/HEAD/worktree/测试 PASS），然后：

```bash
git add notes/owner_b_v26_offline_bundle_wire_preflight.md
git commit -m "docs(preflight): add v26 offline-bundle wire preflight (no-gpu)"
```

---

### Task 2: 最小接线 offline bundle 到 meeting docs（只加“入口 + 校验方式”）

**Files:**
- Modify: `docs/reviews/2026-02-26/meeting-index-v26.md`
- Modify: `docs/reviews/2026-02-26/meeting-handout-v26.md`
- Modify: `docs/reviews/2026-02-26/meeting-checklist-v26.md`
- Modify: `docs/writing/planb_onepager_v26.md`

**Step 1: 依赖检查（local-only，不阻塞提交）**

Run:
```bash
test -f /root/projects/4d-recon/artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz && echo "offline bundle: OK" || echo "offline bundle: MISSING"
```

说明：bundle 缺失也可以提交文档接线，但必须标注为 “local-only（若存在）”。

**Step 2: 修改内容（建议写法，保持最小增量）**

统一新增一条“可选离线 bundle”说明，指向 `notes/planb_meeting_assets_v26_owner_a.md` 作为 SHA 真源：

- 路径：`artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`
- SHA 真源：`notes/planb_meeting_assets_v26_owner_a.md`
- 校验命令（1 行即可）：`sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

建议落点：

- `meeting-index-v26.md`：`Presenter Pack` 下加一条 “Offline bundle (local-only) …”
- `meeting-handout-v26.md`：证据入口或播放清单末尾加一条同样提示
- `meeting-checklist-v26.md`：增加一个 “Optional: offline bundle check” 段落（不改变现有 7 大段结构也可，作为附加段落）
- `planb_onepager_v26.md`：在“证据入口”或“播放清单”下加一条提示（保持 1 行）

**Step 3: 自检（不得出现绝对路径与 TODO）**

Run:
```bash
rg -n "TODO" docs/reviews/2026-02-26/meeting-index-v26.md docs/reviews/2026-02-26/meeting-handout-v26.md docs/reviews/2026-02-26/meeting-checklist-v26.md docs/writing/planb_onepager_v26.md || true
rg -n "/root/projects/4d-recon" docs/reviews/2026-02-26/meeting-index-v26.md docs/reviews/2026-02-26/meeting-handout-v26.md docs/reviews/2026-02-26/meeting-checklist-v26.md docs/writing/planb_onepager_v26.md || true
rg -n "新增 full600 `N=0`" docs/reviews/2026-02-26/meeting-checklist-v26.md docs/reviews/2026-02-26/meeting-handout-v26.md docs/writing/planb_onepager_v26.md
```

Expected:
- 不出现 `TODO`
- 不出现绝对路径 `/root/projects/4d-recon`（文档内保持 repo 相对路径）
- `N=0` 仍存在

**Step 4: Commit**

Run:
```bash
git add docs/reviews/2026-02-26/meeting-index-v26.md \
        docs/reviews/2026-02-26/meeting-handout-v26.md \
        docs/reviews/2026-02-26/meeting-checklist-v26.md \
        docs/writing/planb_onepager_v26.md
git commit -m "docs(review): wire local offline meeting bundle into v26 meeting docs"
```

---

### Task 3: 更新 docs 总索引入口（让 checklist/handout/index 可一键到达）

**Files:**
- Modify: `docs/README.md`

**Step 1: 最小增量**

在 `docs/README.md` 合适位置新增/补充：
- `docs/reviews/2026-02-26/meeting-index-v26.md`
- `docs/reviews/2026-02-26/meeting-handout-v26.md`
- `docs/reviews/2026-02-26/meeting-checklist-v26.md`

**Step 2: Commit**

Run:
```bash
git add docs/README.md
git commit -m "docs(index): link v26 meeting checklist in docs index"
```

---

### Task 4: 最终回归 + 推送合入

**Files:**
- (none)

**Step 1: 全量 tests**

Run:
```bash
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: 全 PASS。

**Step 2: Rebase + Push**

Run:
```bash
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected: push 成功；提交不包含任何 `artifacts/**/*.tar.gz`、`outputs/`、`data/`。

