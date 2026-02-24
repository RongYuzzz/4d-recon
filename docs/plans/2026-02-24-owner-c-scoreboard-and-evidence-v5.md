# Report Scoreboard + Evidence v5 Implementation Plan (Owner C)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不阻塞 A（cue mining v2 / seg2）与 B（strong v2）的情况下，提升“汇报/论文可用”的工程交付面：自动生成 protocol scoreboard（表格 + delta），并在 A/B 新结果落地后快速产出 evidence pack v5（含 docs 快照 + SHA256 登记 + 可复现 runbook 口径）。

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

### Task C27: 新增 scoreboard 生成脚本（protocol v1 一键出 slide 表）

动机：
- `metrics.csv` 可机器读，但现场/写作更需要“自动出一张表 + delta（vs baseline）”。
- 避免手抄指标导致口径漂移。

**Files:**
- Create: `scripts/summarize_scoreboard.py`
- Create: `scripts/tests/test_summarize_scoreboard.py`
- (Optional) Update: `notes/demo-runbook.md`（加 1 条“生成 scoreboard”命令）

**Step 1: 写最小失败用例（先写测试）**
- 目标：构造一个最小 `metrics.csv`，确保脚本能：
  - 只选 `step=599` + `stage=test` 的行；
  - 同时兼容 `outputs/protocol_v1/selfcap_bar_8cam60f/...` 与 `outputs/protocol_v1/gate1/selfcap_bar_8cam60f/...`；
  - 输出 markdown 表格 + delta(vs baseline) 列；
  - 当 `tlpips` 为空时不崩溃（以 `-` 或空值展示）。

**Step 2: 跑测试确认失败**
Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-scoreboard-v5
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- FAIL（缺少 `scripts/summarize_scoreboard.py` 或 import/CLI 不存在）。

**Step 3: 实现最小 CLI（让测试转绿）**
- 输入：
  - `--metrics_csv outputs/report_pack/metrics.csv`
  - `--out_md outputs/report_pack/scoreboard.md`
  - `--protocol_id selfcap_bar_8cam60f_protocol_v1`（可选，仅用于写标题/footnote）
  - `--select_contains selfcap_bar_8cam60f`（默认值；用于同时覆盖 `.../selfcap_bar_8cam60f/...` 与 `.../gate1/selfcap_bar_8cam60f/...`）
  - `--select_prefix outputs/protocol_v1/`（默认值；可选再加一层前缀限制，避免扫到非 protocol 产物）
  - `--step 599`（默认 599）
  - `--stage test`（默认 test）
- 行筛选：
  - 只选 stage/step 匹配的行；
  - 基于 `run_dir` 的 basename 识别并仅保留四条（若存在）：`baseline_600`、`ours_weak_600`、`control_weak_nocue_600`、`ours_strong_600`
- 输出 markdown：
  - 表格列：PSNR/SSIM/LPIPS/tLPIPS + delta(vs baseline)
  - 追加“结论要点”占位（由 C 现场填 3 行 bullet）

**Step 4: 重新跑测试**
Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-scoreboard-v5
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- PASS

**Step 5:（可选）更新 demo-runbook**
- 在 `notes/demo-runbook.md` 增加一条命令（放在 “证据包/报表” 那一段）：
```bash
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md
```

**Step 6: 提交**
Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260224-scoreboard-v5
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py notes/demo-runbook.md
git commit -m "feat(report-pack): add scoreboard summarizer"
```

---

### Task C28: Evidence v5 刷新（等待 A/B 新结果落地后执行）

依赖（由 A/B 产出）：
- A：seg2 runs（`data/selfcap_bar_8cam60f_seg200_260` + baseline/weak 600）
- B：strong v2 attempt（`pred_pred` mode）结果与审计文档

**Step 1: 刷新 report_pack**
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md
```

**Step 2: 生成 v5 evidence tar（只打包必要证据）**
```bash
cd /root/projects/4d-recon
DATE="$(date +%F)"
python3 scripts/pack_evidence.py --repo_root . --out_tar "artifacts/report_packs/report_pack_${DATE}-v5.tar.gz"
sha256sum "artifacts/report_packs/report_pack_${DATE}-v5.tar.gz"
```

**Step 3: SHA256 登记与 docs 快照**
- 更新：`artifacts/report_packs/SHA256SUMS.txt`（只入库校验和）
- 新增：`docs/report_pack/${DATE}-v5/`：
  - `metrics.csv`
  - `scoreboard.md`
  - `ablation_notes.md`
  - `failure_cases.md`
  - `manifest_sha256.csv`

验收：
- tar 内包含：
  - `git_rev.txt`
  - `outputs/report_pack/metrics.csv` + `outputs/report_pack/scoreboard.md`
  - strong v2 的 `outputs/correspondences/**/viz/*`（matching_viz）
  - 关键 run 的 `stats/{val,test}_step0599.json` 与 `videos/traj_4d_step599.mp4`

**Step 4: 提交 docs 快照与 SHA256SUMS**
Run:
```bash
cd /root/projects/4d-recon
git add artifacts/report_packs/SHA256SUMS.txt "docs/report_pack/${DATE}-v5"
git commit -m "docs(report-pack): snapshot v5 metrics/scoreboard and sha256"
```

---

### Task C29: 主线同步（可选，但建议做）

动机：
- 当前 `main` 往往 ahead `origin/main`，多人协作容易分叉。

Run:
```bash
cd /root/projects/4d-recon
git status --porcelain=v1
for t in scripts/tests/test_*.py; do python3 "$t"; done
git push origin main
```

验收：
- push 成功；团队可直接基于 `origin/main` 拉取继续工作。
