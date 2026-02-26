# Writing Mode v25 (Owner B / No-GPU): Template Hygiene 接入 + v25 report-pack/evidence 收口

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 Owner A（GPU0）执行“Plan‑B slice template hygiene（seg400_460 + seg1800_1860）”期间，Owner B（No‑GPU）并行准备并在 A 交付后快速刷新 v25 report-pack/evidence，把“re-template 后的最新 smoke200 指标”纳入 anti‑cherrypick 证据链与写作入口，避免被质疑“Plan‑B 不止替换 velocities”。

**Architecture:** A 会覆盖更新 `outputs/plan_b/<slice>/init_points_planb_step5.npz` 并重跑对应 `outputs/protocol_v1_<slice>/.../planb_init_smoke200`；B 的任务是：刷新 `outputs/report_pack/metrics.csv`、重新生成 `planb_anticherrypick.md` 与 v25 docs 快照/evidence，并在写作文稿中把“template hygiene”声明写清楚。

**Tech Stack:** `scripts/build_report_pack.py`、`scripts/summarize_planb_anticherrypick.py`、`scripts/summarize_scoreboard.py`、`scripts/pack_evidence.py`、`scripts/tests/test_*.py`、`docs/report_pack/*`、`notes/*`。

---

## 硬约束（违反即不可比）

1. 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`）。
2. 不改协议、不改数据：`docs/protocols/protocol_v1.yaml` 不动；不触碰 `data/selfcap_bar_8cam60f` 分布口径。
3. 不提交 `data/`、`outputs/`、`*.tar.gz`；仅提交 `scripts/`、`docs/`、`notes/`、`artifacts/report_packs/SHA256SUMS.txt`。
4. 不引入新 full600 预算口径。

---

## 依赖（来自 A）

Owner A 将按 `docs/plans/2026-02-26-owner-a-planb-template-hygiene-rerun-seg400-seg1800.md` 交付：
- 重新生成的 slice baseline 模板：
  - `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init/keyframes_60frames_step5.npz`
  - `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/_baseline_init/keyframes_60frames_step5.npz`
- 覆盖更新的 Plan‑B init：
  - `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/init_points_planb_step5.npz`
  - `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/init_points_planb_step5.npz`
- 重跑后的 smoke200 关键产物：
  - `outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/stats/test_step0199.json`
  - `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/stats/test_step0199.json`
- 更新后的 `notes/*` 与 `Progress.md`（包含“re-template 后”的新数值与结论）

---

### Task B101: 建立隔离 worktree + 预检对齐

**Files:**
- Create: `notes/owner_b_v25_preflight.md`

**Steps**
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260226-writing-mode-v25 origin/main
cd .worktrees/owner-b-20260226-writing-mode-v25

python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

在 `notes/owner_b_v25_preflight.md` 记录：
- HEAD + 最近 5 条提交
- 4 个测试 PASS

---

### Task B102: 写作口径补一条“template hygiene”声明（不改结论，只加防守句）

**Files:**
- Modify: `notes/planb_verdict_writeup_owner_b.md`
- Modify: `docs/writing/planb_paper_outline.md`

**Edits（建议直接复制粘贴句子，避免含糊）**
- 在 verdict writeup 增加一段：
  - “为排除 ‘模板来自 canonical’ 的质疑，我们对 seg400_460 与 seg1800_1860 重做了 template hygiene：使用该 slice 自己的 baseline init（positions/colors/times/durations）作为模板，仅替换 velocities，并重跑 planb_init_smoke200；v25 以 re-template 后的结果为准。”
- 在 paper outline 的方法或实验段增加同一句，并指向 v25 快照入口（见 B104）。

**Commit**
```bash
git add notes/planb_verdict_writeup_owner_b.md docs/writing/planb_paper_outline.md
git commit -m "docs(planb): add template-hygiene defense note for seg slices"
```

---

### Task B103: 等待依赖到位后，刷新 report-pack/evidence v25

**Precheck（必须满足）**
```bash
cd /root/projects/4d-recon
test -f outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/stats/test_step0199.json
test -f outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/stats/test_step0199.json
```

**Commands（以主仓 outputs 为源）**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v25

python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md

python3 scripts/pack_evidence.py \
  --repo_root /root/projects/4d-recon \
  --out_tar artifacts/report_packs/report_pack_2026-02-26-v25.tar.gz
```

**Docs 快照（manifest 从 tar 解包）**
- New: `docs/report_pack/2026-02-26-v25/`
  - `metrics.csv`
  - `scoreboard.md`
  - `planb_anticherrypick.md`
  - `ablation_notes.md`
  - `failure_cases.md`
  - `manifest_sha256.csv`

**SHA 登记**
- Modify: `artifacts/report_packs/SHA256SUMS.txt`（追加 v25 行）

**验收**
- `docs/report_pack/2026-02-26-v25/planb_anticherrypick.md` 中 seg400_460/seg1800_1860 的 delta 与 `Progress.md` 中 “re-template 后”口径一致。
- `docs/report_pack/2026-02-26-v25/manifest_sha256.csv` 包含对应两条 `stats/test_step0199.json` 与 `videos/traj_4d_step199.mp4`。

---

### Task B104: v25 快照口径检查（标题/版本号/引用一致）

**Why:** v24 的 `ablation_notes.md`/`failure_cases.md` 标题仍是 v23，容易引起审阅疑问；v25 需自洽。

**Edits**
- 若 `outputs/report_pack/ablation_notes.md` 或 `outputs/report_pack/failure_cases.md` 标题版本号不正确：
  - 在生成 v25 前修正为 “v25”（或版本中性 “Writing Mode 2026-02-26”），并补一句：本次 v25 为 template hygiene 刷新（seg400_460/seg1800_1860）。
- 确保 v25 `docs/report_pack/...` 内标题与内容一致（不再出现 “v23”）。

---

### Task B105: 回归 + 合入 main

**Steps**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v25
for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1
git push origin HEAD:main
```

Expected:
- tests 全 PASS
- `git status` 无意外脏文件
- push 成功

