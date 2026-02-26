# Writing Mode v26: Pack Re-template Hygiene + Prep seg300_360 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不使用 GPU 的前提下，修复当前主线“写作口径/Progress vs report-pack v25 快照不一致”的问题：刷新一版 `v26` report-pack/evidence，使 `seg400_460/seg1800_1860` 的 anti-cherrypick delta 与 A 的 template hygiene（仅替换 velocities 的 re-template）一致；同时把 `seg300_360` 作为“额外切片”显示在 anti-cherrypick 汇总中（为 A 的 seg300_360 smoke200 预留入口）。

**Architecture:** 先做一次很小的 report 逻辑增强：`scripts/summarize_planb_anticherrypick.py` 在 seg600 已存在时也能显示 seg300_360（若缺失则标注 missing，不崩）。随后用主阵地 `outputs/` 重建 `outputs/report_pack/*`，打包 evidence tar（不入库）并生成 `docs/report_pack/2026-02-26-v26/*` 快照与 `SHA256SUMS.txt` 条目，最后更新写作入口文稿指向 v26。

**Tech Stack:** `scripts/build_report_pack.py`、`scripts/summarize_scoreboard.py`、`scripts/summarize_planb_anticherrypick.py`、`scripts/pack_evidence.py`、`scripts/tests/test_*.py`。

---

## Hard Constraints（违反即不可比）

1. 全程 No-GPU；不改训练数值逻辑、不改 `docs/protocols/protocol_v1.yaml`。
2. 不新增训练、不改 `data/`、不提交 `outputs/`、不提交 `artifacts/report_packs/*.tar.gz`。
3. 交付必须可审计：命令、HEAD、关键路径、delta 自检、tests PASS、commit 可追溯。

---

## Task B111：建立隔离 worktree + 预检

**Files**
- Create: `notes/owner_b_v26_preflight.md`

**Steps**
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260226-writing-mode-v26 origin/main
cd .worktrees/owner-b-20260226-writing-mode-v26

# 共享主阵地大目录（避免 worktree 下 outputs/data 空壳）
test -e outputs || ln -s /root/projects/4d-recon/outputs outputs
test -e data || ln -s /root/projects/4d-recon/data data

# provenance（写入 notes/owner_b_v26_preflight.md）
git rev-parse HEAD
git log -n 5 --oneline

# 最小预检
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: 全 PASS。

---

## Task B112：让 anti-cherrypick 汇总“同时显示 seg300_360”（TDD）

> 目的：A 后续补齐 `seg300_360` smoke200 后，不需要再改脚本即可被 report-pack 自动收录为“额外切片证据位”。

**Files**
- Modify: `scripts/tests/test_summarize_planb_anticherrypick.py`
- Modify: `scripts/summarize_planb_anticherrypick.py`

**Step 1: 先改测试制造红灯**
- 在 `scripts/tests/test_summarize_planb_anticherrypick.py` 的 dummy `metrics.csv` 里已经同时包含 seg600_660 与 seg300_360 的情况下，要求输出 markdown 中必须出现 `## seg300_360`（或 `## seg300_360 (missing)`，按实现选择，但建议固定为 `## seg300_360`）。

Run:
```bash
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```
Expected: FAIL（缺少 seg300 section）。

**Step 2: 最小实现**
- 修改 `scripts/summarize_planb_anticherrypick.py`：
  - 保留现有逻辑：seg600_660 仍是主段落（优先）。
  - 新增逻辑：若 `seg300_360` rows 存在，则 **额外 append** 一段 `seg300_360`（非 fallback）。
  - 若 seg300 缺失，则输出 `seg300_360 (missing)` 也可，但不要崩溃。

**Step 3: 绿灯**
```bash
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```
Expected: PASS。

**Step 4: Commit**
```bash
git add scripts/summarize_planb_anticherrypick.py scripts/tests/test_summarize_planb_anticherrypick.py
git commit -m "feat(report-pack): always render seg300_360 section in planb anti-cherrypick summary"
```

---

## Task B113：刷新主阵地 report-pack（对齐 re-template 数值）

**Why:** 当前 `docs/report_pack/2026-02-26-v25/*` 是 A re-template 之前生成的，导致 seg400/seg1800 的 delta 仍为旧值；需要新快照对齐 `Progress.md` 与 `notes/anti_cherrypick_seg*.md` 的最新口径。

**Steps**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26

# 1) 重建 metrics.csv（显式指定 outputs_root，避免 worktree 空壳）
python3 scripts/build_report_pack.py \
  --outputs_root /root/projects/4d-recon/outputs \
  --out_dir /root/projects/4d-recon/outputs/report_pack

# 2) 重建 scoreboard.md
python3 scripts/summarize_scoreboard.py \
  --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv \
  --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md

# 3) 重建 planb_anticherrypick.md
python3 scripts/summarize_planb_anticherrypick.py \
  --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv \
  --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md
```

**自检（必须写入后续 commit message/notes 或 checklist）**
- `outputs/report_pack/planb_anticherrypick.md` 中：
  - `seg400_460` delta == `ΔPSNR=+0.1845, ΔLPIPS=-0.0481, ΔtLPIPS=-0.0516`（允许四舍五入末位差异）
  - `seg1800_1860` delta == `ΔPSNR=+0.1799, ΔLPIPS=-0.0489, ΔtLPIPS=-0.0549`
- `notes/planb_verdict_writeup_owner_b.md` 不再声称“v25 以 re-template 为准”（需要改为 v26）。

---

## Task B114：刷新 v26 evidence tar + 登记 SHA（tar 不入库）

**Files**
- Modify: `artifacts/report_packs/SHA256SUMS.txt`

**Steps**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26

python3 scripts/pack_evidence.py \
  --repo_root /root/projects/4d-recon \
  --out_tar /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz

sha256sum /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz | tee /tmp/v26.sha
cat /tmp/v26.sha >> /root/projects/4d-recon/artifacts/report_packs/SHA256SUMS.txt
```

Expected:
- tar 成功生成（本地文件存在）
- `SHA256SUMS.txt` 新增 v26 行

---

## Task B115：生成 docs 快照 v26（入库）

**Files**
- Create: `docs/report_pack/2026-02-26-v26/ablation_notes.md`
- Create: `docs/report_pack/2026-02-26-v26/failure_cases.md`
- Create: `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`
- Create: `docs/report_pack/2026-02-26-v26/metrics.csv`
- Create: `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- Create: `docs/report_pack/2026-02-26-v26/scoreboard.md`

**Steps**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26

SNAP=docs/report_pack/2026-02-26-v26
mkdir -p "$SNAP"

cp -av /root/projects/4d-recon/outputs/report_pack/metrics.csv "$SNAP/metrics.csv"
cp -av /root/projects/4d-recon/outputs/report_pack/scoreboard.md "$SNAP/scoreboard.md"
cp -av /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md "$SNAP/planb_anticherrypick.md"
cp -av /root/projects/4d-recon/outputs/report_pack/ablation_notes.md "$SNAP/ablation_notes.md"
cp -av /root/projects/4d-recon/outputs/report_pack/failure_cases.md "$SNAP/failure_cases.md"

# manifest 来自 tar（pack_evidence 内置生成）
tar -xzf /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz \
  -O manifest_sha256.csv > "$SNAP/manifest_sha256.csv"
```

**验收要点**
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md` 的 seg400/seg1800 delta 与 `Progress.md` 一致（re-template 口径）。
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv` 非空。

---

## Task B116：修正写作口径入口（指向 v26，避免错误引用 v25）

**Files**
- Modify: `notes/planb_verdict_writeup_owner_b.md`
- Modify: `docs/writing/planb_paper_outline.md`

**Edits**
- 把文内 “v25 以 re-template 后为准” 的引用全部改为 `v26`（因为 v25 快照生成早于 A re-template）。
- 更新 seg400_460、seg1800_1860 的 delta 数值为 re-template 后版本（与 `Progress.md`/`v26 planb_anticherrypick.md` 同步）。
- 主证据链接从 `docs/report_pack/2026-02-26-v24/*`、`...-v25/*` 统一升级为 `...-v26/*`（必要处保留历史链接，但默认只给 v26）。

---

## Task B117：回归测试 + 提交 + 推送 main

**Steps**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26

# 回归（至少覆盖 pack/report/scoreboard/anticherrypick）
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py

git status --porcelain=v1
```

**Commit（建议拆两次）**
1) 报表脚本改动（已在 Task B112 提交）
2) v26 快照与写作更新：
```bash
git add \
  docs/report_pack/2026-02-26-v26 \
  artifacts/report_packs/SHA256SUMS.txt \
  notes/owner_b_v26_preflight.md \
  notes/planb_verdict_writeup_owner_b.md \
  docs/writing/planb_paper_outline.md
git commit -m "docs(report-pack): snapshot v26 aligned with template-hygiene reruns"
git push origin HEAD:main
```

---

## Follow-up（阻塞于 A 的 seg300_360 smoke200）

当 A 按 `docs/plans/2026-02-26-owner-a-planb-seg300_360-smoke200-and-handoff.md` 交付后：
- 仅需重复 Task B113-B115（新版本号建议 `v27`），即可把 `seg300_360` 的真实数值纳入 `planb_anticherrypick.md` 与 evidence 证据链（无需再改脚本）。

