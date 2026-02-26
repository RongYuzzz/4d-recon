# Writing Mode v24 (Owner B / No-GPU): seg1800_1860 防守位接入 + v24 report-pack/evidence 收口

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 Owner A（GPU0）跑 `seg1800_1860` smoke200 的同时（不新增 full600），Owner B（No‑GPU）并行准备并最终刷新 v24 report-pack/evidence，把新增 anti‑cherrypick 防守位与（可选）定性 side-by-side 入口纳入写作链路。

**Architecture:** 扩展 `scripts/summarize_planb_anticherrypick.py` 增加 `seg1800_1860` 小节（TDD）；更新 `docs/execution/2026-02-26-planb-qualitative.md` 增加 seg1800_1860 的 side-by-side 命令；等待 A 产物到位后，重刷 `outputs/report_pack/*`（metrics/scoreboard/planb_anticherrypick）并打包 `report_pack_2026-02-26-v24.tar.gz`，落 `docs/report_pack/2026-02-26-v24/` 快照与 SHA。

**Tech Stack:** `scripts/build_report_pack.py`、`scripts/summarize_scoreboard.py`、`scripts/summarize_planb_anticherrypick.py`、`scripts/pack_evidence.py`、`scripts/make_side_by_side_video.sh`、`scripts/tests/test_*.py`。

---

## 硬约束（违反即不可比）

1. 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`）。
2. 不改协议、不改数据：`docs/protocols/protocol_v1.yaml` 不动；不触碰 canonical `data/selfcap_bar_8cam60f` 分布口径。
3. 不提交 `data/`、`outputs/`、`*.tar.gz`；仅提交 `scripts/`、`docs/`、`notes/`、`artifacts/report_packs/SHA256SUMS.txt`。
4. full600 预算为 0：不提出“补 full600”需求；如需新增 full600 必须新决议文件。

---

## 依赖（来自 A，产物到位后才能执行 v24 最终刷新）

Owner A 将按 `docs/plans/2026-02-26-owner-a-planb-seg1800_1860-smoke200-and-handoff.md` 交付：
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/{baseline_smoke200,planb_init_smoke200}/videos/traj_4d_step199.mp4`
- `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json`
- `notes/anti_cherrypick_seg1800_1860.md`
- `notes/handoff_planb_seg1800_1860_owner_a.md`

（可选）若 A 额外生成 side-by-side，本机应出现：
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4`

---

### Task B91: 建立隔离 worktree + 预检对齐

**Files:**
- Create: `notes/owner_b_v24_preflight.md`

**Step 1: 新建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260226-writing-mode-v24 origin/main
cd .worktrees/owner-b-20260226-writing-mode-v24
```

**Step 2: 基线回归（No‑GPU）**

Run:
```bash
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: PASS。

**Step 3: 记录 provenance**

写入 `notes/owner_b_v24_preflight.md`：
- `git rev-parse HEAD`
- `git log -n 5 --oneline`
- 上述测试 PASS 结论

---

### Task B92: 扩展 anti-cherrypick 汇总脚本纳入 seg1800_1860（TDD）

**Files:**
- Modify: `scripts/summarize_planb_anticherrypick.py`
- Modify: `scripts/tests/test_summarize_planb_anticherrypick.py`

**Step 1: 写红灯测试（seg1800_1860 小节）**

在 `scripts/tests/test_summarize_planb_anticherrypick.py` 的 dummy metrics rows 中新增：
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/{baseline_smoke200,planb_init_smoke200}` 的 test@199 两行

并断言 markdown 中存在：
- `## seg1800_1860`
- 且该 section 含 `ΔPSNR/ΔLPIPS/ΔtLPIPS`

Run:
```bash
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```
Expected: FAIL（缺少 seg1800_1860 section）。

**Step 2: 最小实现**

在 `scripts/summarize_planb_anticherrypick.py`：
- `_filter_group` 增加 `seg1800_1860` 分支（匹配 `selfcap_bar_8cam60f_seg1800_1860`）
- `main()` 里在 seg600_660 之后追加一段：
  - 若存在 seg1800_1860 rows，则 `_append_group(lines, "seg1800_1860", ...)`
  - 否则 `_append_group(lines, "seg1800_1860 (missing)", [])`（不崩溃，便于写作时显式说明缺失）

**Step 3: 绿灯**

Run:
```bash
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```
Expected: PASS。

**Step 4: Commit**

Run:
```bash
git add scripts/summarize_planb_anticherrypick.py scripts/tests/test_summarize_planb_anticherrypick.py
git commit -m "feat(report-pack): extend planb anti-cherrypick summary with seg1800_1860"
```

---

### Task B93: 补齐定性 runbook（seg1800_1860 side-by-side 入口）

**Files:**
- Modify: `docs/execution/2026-02-26-planb-qualitative.md`

**Step 1: 增加 seg1800_1860 命令段**

新增小节（仿照 seg600_660），命令为：
```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/videos/traj_4d_step199.mp4 \
  --right outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg1800_1860_step199.mp4 \
  --left_label baseline_seg1800_1860_smoke200 \
  --right_label planb_seg1800_1860_smoke200 \
  --overwrite
```

**Step 2: Commit**

Run:
```bash
git add docs/execution/2026-02-26-planb-qualitative.md
git commit -m "docs(qualitative): add seg1800_1860 side-by-side command"
```

---

### Task B94: 等待依赖到位后，生成 seg1800_1860 side-by-side（本地产物，不入库）

**Files:**
- None

**Precheck**
```bash
cd /root/projects/4d-recon
test -f outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/videos/traj_4d_step199.mp4
test -f outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/videos/traj_4d_step199.mp4
```

**Run（生成 side-by-side mp4）**
```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/videos/traj_4d_step199.mp4 \
  --right outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg1800_1860_step199.mp4 \
  --left_label baseline_seg1800_1860_smoke200 \
  --right_label planb_seg1800_1860_smoke200 \
  --overwrite
```

Expected:
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4` 存在

Note:
- mp4 不入库；但 `scripts/pack_evidence.py` 会在存在时自动收录。

---

### Task B95: 刷新 v24 report-pack/evidence（依赖 A 产物到位）

**Precheck（必须满足）**
- `outputs/protocol_v1_seg1800_1860/.../stats/test_step0199.json` 两条存在

**Commands（以主仓 outputs 为源；允许 worktree 执行，但用主仓路径）**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v24

python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md

python3 scripts/pack_evidence.py \
  --repo_root /root/projects/4d-recon \
  --out_tar artifacts/report_packs/report_pack_2026-02-26-v24.tar.gz
```

**Docs 快照落盘（manifest 从 tar 解包）**
- New: `docs/report_pack/2026-02-26-v24/`
  - `metrics.csv`
  - `scoreboard.md`
  - `planb_anticherrypick.md`
  - `ablation_notes.md`
  - `failure_cases.md`
  - `manifest_sha256.csv`

**SHA 登记**
- Modify: `artifacts/report_packs/SHA256SUMS.txt`（追加 v24 行）

**验收**
- `docs/report_pack/2026-02-26-v24/planb_anticherrypick.md` 出现 `seg1800_1860` 小节与 delta
- `docs/report_pack/2026-02-26-v24/metrics.csv` 可 grep 到 `protocol_v1_seg1800_1860` 的 test@199 行
- `docs/report_pack/2026-02-26-v24/manifest_sha256.csv` 包含新增 seg 的 `stats/test_step0199.json` 与 `videos/traj_4d_step199.mp4`

---

### Task B96: 写作入口更新（只扩防守位，不改主结论）

**Files:**
- Modify: `notes/planb_verdict_writeup_owner_b.md`
- Modify: `docs/writing/planb_paper_outline.md`

**Step 1: 更新写作口径**
- 在 verdict writeup 增加 seg1800_1860 smoke200 一段（或标记 missing）
- 在 outline 的 anti‑cherrypick 列表中加入 seg1800_1860，并指向 v24 证据路径

**Step 2: Commit**
```bash
git add notes/planb_verdict_writeup_owner_b.md docs/writing/planb_paper_outline.md
git commit -m "docs(planb): extend anti-cherrypick defense with seg1800_1860"
```

---

### Task B97: 全量回归 + 合入 main

**Step 1: 全量测试**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v24
for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1
```

Expected:
- tests 全 PASS
- `git status` 仅包含预期变更

**Step 2: 合入 main**
```bash
git push origin HEAD:main
```

