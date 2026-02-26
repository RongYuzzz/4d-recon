# Writing Mode + 失败归因最小包 + 报表链路更新 Implementation Plan（Owner B / No‑GPU）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 B 无 GPU 的约束下，支撑 02‑26 决议（Plan‑B 48h timebox + Writing Mode）：补齐“失败归因最小包”与报表/证据链的必要工具与文档，确保 A 跑完 Plan‑B 后可以**最快速度**刷新 report-pack、生成可辩护的写作材料（含防守口径）。

**Architecture:** 不改 `protocol_v1` / 不改 `data/`；B 的工作以“工具/文档/报表自动化”为主，尽量在 A 跑 GPU 期间完成。对需要 A 输出的步骤，写成“等 A 完成后 10 分钟内可执行”的收口任务。

**Tech Stack:** Python（纯 CPU）、TensorBoard event 解析（仅导出 CSV/PNG，不打包 raw tb）、report-pack（`scripts/build_report_pack.py`/`scripts/summarize_scoreboard.py`/`scripts/pack_evidence.py`）、现有输出日志（`run.log`、`tb/events.*`、`stats/*.json`）。

---

## 前置硬约束（违反即不可比/信息污染）

1. 决议真源：
   - `docs/decisions/2026-02-26-planb-pivot.md`
2. 叙事纪律：
   - 禁止 “零速陷阱/零速已证实”；统一改为 **velocity prior 质量/尺度/一致性不足或噪声过大**（见决议）。
3. 证据链纪律：
   - 不入库大文件：不提交 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只提交 `docs/*`、`notes/*`、`artifacts/report_packs/SHA256SUMS.txt`。
4. feature‑loss 冻结：
   - 禁止新增 feature‑loss full600；只允许做不耗 full600 的失败归因统计/可视化（writing defense）。

---

### Task 1: 建立隔离执行环境（No‑GPU）

**Files:**
- Create: `notes/owner_b_writing_mode_preflight.md`

**Step 1: 建立干净 worktree**

Run：
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260226-writing-mode origin/main
cd .worktrees/owner-b-20260226-writing-mode
```

**Step 2: 记录 provenance**

Run：
```bash
git rev-parse HEAD
git log -n 5 --oneline
```

**Step 3: 最小回归（确保主线没坏）**

Run：
```bash
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected：全部 PASS。

---

### Task 2: 报表“主视图”修正：scoreboard 默认纳入 Plan‑B + 缺项时不误报风险

> 背景：当前 `scripts/summarize_scoreboard.py` 只保留 CORE_RUNS/strong/feature_loss 等，**不会自动展示 `planb_init_600`**；且当 `ours_weak_600` 缺失时会输出“未发现风险信号”，存在误导风险。

**Files:**
- Modify: `scripts/summarize_scoreboard.py`
- Modify: `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 先写失败用例（红灯）**

目标：
- `planb_init_600` 在 metrics.csv 中存在时，scoreboard 必须包含它。
- 当缺少 `ours_weak_600` 或 `control_weak_nocue_600` 时，风险提示必须输出 “无法判断：缺少 XXX”，而不是 “未发现风险信号”。

**Step 2: 实现最小修复**

建议改动点：
- 扩展 `CORE_RUNS`：加入 `planb_init_600`（以及可选 `planb_init_600` 的其他命名约定）。
- 添加 `_is_planb_variant(run_name)` + 纳入 `_keep_run`。
- 风险提示逻辑增加缺项分支：
  - 仅当 control 与 ours_weak 都存在且可比时才做 risk 判定
  - 否则输出缺项提示

**Step 3: 跑测试与提交**

Run：
```bash
python3 scripts/tests/test_summarize_scoreboard.py
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py
git commit -m "fix(scoreboard): include planb runs and avoid false risk hints on missing cores"
```

---

### Task 3: 失败归因最小包（Feature‑loss）工具化（不跑 GPU）

> 目标：满足 `meeting-decision.md` 的“5 项最小失败归因包”，用于写作防守，证明 pivot 不是“实现 bug 逃避”。

**Files:**
- Create: `scripts/export_tb_scalars.py`
- Create: `scripts/tests/test_export_tb_scalars.py`
- Create: `notes/feature_loss_failure_attribution_minpack.md`

**Step 1: 写失败测试（红灯）**

测试思路（不依赖真实 outputs）：
- 用 tensorboard writer 在临时目录生成一个最小 event file（写入 2-3 个 scalar tag，含 step）。
- 调用 `scripts/export_tb_scalars.py` 导出为 CSV（或 JSON），断言：
  - tags 选择生效
  - step/值数量正确
  - 缺失 tag 时行为为“跳过 + 给出 warning”，不崩溃

**Step 2: 实现 `export_tb_scalars.py`**

最低功能（足够写作）：
- 输入：`--run_dir <outputs/.../xxx_600>` 或 `--tb_dir <.../tb>`
- 选择 tags（默认导出）：
  - `loss/total`
  - `loss/l1_raw`
  - `loss/feat_raw`
  - `loss_weighted/l1`
  - `loss_weighted/feat`
- 输出：
  - `<out_dir>/<run_name>_tb_scalars.csv`
  - 可选：`<out_dir>/<run_name>_loss_curves.png`（matplotlib，CPU）

**Step 3: 写入 “失败归因最小包”文档**

在 `notes/feature_loss_failure_attribution_minpack.md` 写清楚 5 项归因（对应 `meeting-decision.md`）与执行命令：
1. loss 量级曲线（photo vs feat）来自 tb 导出的 CSV/图
2. cache round-trip（已有 sanity 脚本路径引用即可）
3. 1–2px 平移敏感性（若暂无脚本，写为“可选加分项”并给最小实现思路）
4. gating/patch 命中率热图（若暂无脚本，写为“待补/可选”并给数据源）
5. 梯度链检查（10 step 小跑打印 norm；可引用既有 t0/feature-loss hooks 或写最小 patch 方案，但本 task 不触碰训练数值逻辑）

**Step 4: 跑测试与提交**

Run：
```bash
python3 scripts/tests/test_export_tb_scalars.py
git add scripts/export_tb_scalars.py scripts/tests/test_export_tb_scalars.py notes/feature_loss_failure_attribution_minpack.md
git commit -m "feat(diagnostics): export tensorboard scalars for feature-loss failure attribution"
```

---

### Task 4: Plan‑B 写作材料收口（等 A 跑完后 10 分钟内可执行）

**Files:**
- Create: `notes/planb_verdict_writeup_owner_b.md`
- Modify: `outputs/report_pack/ablation_notes.md`（仅在本地；文本快照入库由后续步骤完成）
- Modify: `outputs/report_pack/failure_cases.md`（同上）

**Step 1: 等待 A 输出就绪（不阻塞前 3 个 task）**

需要 A 输出的路径（A 计划里会写入 handoff）：
- `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/stats/test_step0599.json`
- `outputs/protocol_v1_seg200_260/.../control_weak_nocue_600/stats/test_step0599.json`

**Step 2: 刷新 report-pack + scoreboard + evidence**

Run：
```bash
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py
python3 scripts/pack_evidence.py
```

**Step 3: 生成 docs 快照（新版本号 v16 或按当天递增）**

Run（示例）：
```bash
SNAP=docs/report_pack/2026-02-26-v16
mkdir -p "$SNAP"
cp -f outputs/report_pack/metrics.csv "$SNAP/metrics.csv"
cp -f outputs/report_pack/scoreboard.md "$SNAP/scoreboard.md"
cp -f outputs/report_pack/ablation_notes.md "$SNAP/ablation_notes.md"
cp -f outputs/report_pack/failure_cases.md "$SNAP/failure_cases.md"
cp -f outputs/report_pack/manifest_sha256.csv "$SNAP/manifest_sha256.csv"
```

**Step 4: 写入 Plan‑B verdict 短文（用于导师/答辩）**

在 `notes/planb_verdict_writeup_owner_b.md` 写：
- Go/No-Go（按 `docs/decisions/2026-02-26-planb-pivot.md` 的 48h 口径）
- 四行关键对比（baseline/control/planb/seg2-control）
- “为什么这不是零速问题”的一句话口径

**Step 5: 提交（只提交文本，不提交 tar.gz）**

Run：
```bash
git add docs/report_pack/2026-02-26-v16 notes/planb_verdict_writeup_owner_b.md artifacts/report_packs/SHA256SUMS.txt
git commit -m "docs(report-pack): snapshot planb verdict and seg2 defense (2026-02-26-v16)"
```

---

## 并行性说明（为什么 B 不会阻塞 A）

- Task 1–3 完全不依赖 GPU 输出，可与 A 的 Gate‑B1/B2 并行推进。
- Task 4 仅在 A 输出落地后执行，且设计为 “10 分钟内收口刷新”，不占 GPU。

