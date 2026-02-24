# Report Scoreboard + Evidence v5 Implementation Plan (Owner C)

> 状态：部分已完成（截至 `2026-02-24`：scoreboard 相关脚本已合入 `main`，`docs/report_pack/` 已有 `v5-v7` 快照；下一次刷新目标为 **evidence v8**，等待 A/B 新结果落地后执行）。

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不阻塞 A（cue mining v2 / seg2 / velocity stats）与 B（VGGT feature metric loss 主线）的情况下，提升“汇报/论文可用”的工程交付面：自动生成 protocol scoreboard（表格 + delta），并在 A/B 新结果落地后快速产出 **evidence pack v8**（含 docs 快照 + SHA256 登记 + 可复现 runbook 口径）。

**Architecture:** Owner C 负责 `report_pack` 与 `evidence tar` 的可复现与可审计闭环：
- 统一从 `outputs/**/stats/*_step*.json` 生成 `outputs/report_pack/metrics.csv`
- 从 `metrics.csv` 生成一张“可直接上 slide 的 scoreboard（md）”
- v5 evidence pack 只做“刷新与收敛”（不改 protocol v1，本轮不新增算法）

**Tech Stack:** Python（csv/json）、Bash、现有脚本（`scripts/build_report_pack.py`、`scripts/pack_evidence.py`）、脚本级测试（`scripts/tests/*.py`）。

---

### Task C26: 建隔离 worktree（避免污染 main）

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-c-20260224-scoreboard-v5 .worktrees/owner-c-20260224-scoreboard-v5 main
git -C .worktrees/owner-c-20260224-scoreboard-v5 status --porcelain=v1
```

Expected:
- worktree 干净（无未提交改动）。

---

### Task C27: Scoreboard 脚本审计与小修（DONE: 已合入 main；本任务只做维护）

动机：
- `metrics.csv` 可机器读，但现场/写作更需要“自动出一张表 + delta（vs baseline）”。
- 避免手抄指标导致口径漂移。

**Files:**
- Maintain: `scripts/summarize_scoreboard.py`
- Maintain: `scripts/tests/test_summarize_scoreboard.py`
- Maintain: `notes/demo-runbook.md`

**Step 1: 写最小失败用例（先写测试）**
- 目标：构造一个最小 `metrics.csv`，确保脚本能：
  - 只选 `step=599` + `stage=test` 的行；
  - 同时兼容 `outputs/protocol_v1/selfcap_bar_8cam60f/...` 与 `outputs/protocol_v1/gate1/selfcap_bar_8cam60f/...`；
  - 输出 markdown 表格 + delta(vs baseline) 列；
  - 当存在多个 strong 变体（如 `ours_strong_600` / `ours_strong_v2_600`）时，不会因为“只认一个 basename”而漏报；
  - 当存在 feature loss 变体（`feature_loss_v1_600` / `feature_loss_v1_gated_600`）时，能被纳入 scoreboard；
  - 生成 “风险提示” 区块：显式标红 `control > ours_weak`（提醒 cue/注入方式可能拖后腿）；
  - 当 `tlpips` 为空时不崩溃（以 `-` 或空值展示）。

**Step 1: 跑单测确认 scoreboard contract 仍成立**
Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-scoreboard-v5
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- PASS

**Step 2:（可选）更新 demo-runbook**
- 在 `notes/demo-runbook.md` 增加一条命令（放在 “证据包/报表” 那一段）：
```bash
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md
```

**Step 3:（可选）若有改动则提交**
Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-scoreboard-v5
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py notes/demo-runbook.md
git commit -m "feat(report-pack): add scoreboard summarizer"
```

---

### Task C28: Evidence v5 刷新（等待 A/B 新结果落地后执行）

依赖（由 A/B 产出）：
- A：`notes/velocity_stats_selfcap_bar_8cam60f.md`（新）以及 seg2 现有结论 `notes/anti_cherrypick_seg200_260.md`
- B：`feature_loss_v1_600`（以及可选 gated 版本）的 full run 结果与审计文档 `notes/feature_loss_v1_attempt.md`
- （可选）strong attempt 的可审计产物（若存在则纳入，不作为硬依赖）

**Step 1: 刷新 report_pack**
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md
```

**Step 2: 生成 v8 evidence tar（只打包必要证据，避免覆盖既有 v7）**
```bash
cd /root/projects/4d-recon
DATE="$(date +%F)"
python3 scripts/pack_evidence.py --repo_root . --out_tar "artifacts/report_packs/report_pack_${DATE}-v8.tar.gz"
sha256sum "artifacts/report_packs/report_pack_${DATE}-v8.tar.gz"
```

**Step 3: SHA256 登记与 docs 快照**
- 更新：`artifacts/report_packs/SHA256SUMS.txt`（只入库校验和）
- 新增：`docs/report_pack/${DATE}-v8/`：
  - `metrics.csv`
  - `scoreboard.md`
  - `ablation_notes.md`
  - `failure_cases.md`
  - `manifest_sha256.csv`

验收：
- tar 内包含：
  - `git_rev.txt`
  - `outputs/report_pack/metrics.csv` + `outputs/report_pack/scoreboard.md`
  - feature loss v1 的关键 runs（`stats/*.json` + `videos/*.mp4`）
  - （可选）strong attempt 的 `outputs/correspondences/**/viz/*`（matching_viz）
  - 关键 run 的 `stats/{val,test}_step0599.json` 与 `videos/traj_4d_step599.mp4`
  - 新增的 defense notes（若存在则纳入）：`notes/velocity_stats_selfcap_bar_8cam60f.md`

**Step 4: 提交 docs 快照与 SHA256SUMS**
Run:
```bash
cd /root/projects/4d-recon
git add artifacts/report_packs/SHA256SUMS.txt "docs/report_pack/${DATE}-v8"
git commit -m "docs(report-pack): snapshot v8 metrics/scoreboard and sha256"
```

---

### Task C29: 主线同步（可选，但建议做）

动机：
- 当前 `main` 往往 ahead `origin/main`，多人协作容易分叉。

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git log --oneline --decorate --left-right origin/main...main | head
git status --porcelain=v1
for t in scripts/tests/test_*.py; do python3 "$t"; done
# 仅在 fast-forward 且团队确认后再 push：
# git push origin main
```

验收：
- push 成功；团队可直接基于 `origin/main` 拉取继续工作。
