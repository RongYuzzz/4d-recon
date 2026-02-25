# Feature-Loss v2（No-GPU）诊断与效率工具链 Implementation Plan（Owner B）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不占用 GPU 的前提下，补齐 v2 实验的“可比性/可审计/效率”工具链：统一吞吐统计、把吞吐纳入 evidence pack、提供 smoke200（M1）自动对比与 Pareto（PSNR vs tLPIPS）输出，减少 A 的 GPU 浪费与口径错误。

**Architecture:** 所有改动默认不影响训练数值（只新增统计输出/报表脚本）；通过小型 Python 工具脚本 + 单测锁死行为；runner 仅在训练结束后写 `stats/throughput.json` 与复制必要元信息。

**Tech Stack:** Python（stdlib 为主）、现有 `scripts/*` 工具链、`scripts/tests/test_*.py`（逐个执行）。

---

## 并行性说明（与 Owner A 的并行关系）

- 本计划全程不需要 GPU，可与 A 的 `feature-loss v2 postfix` GPU 复核并行推进。
- 产出会直接降低 A 侧的人工对比/误判风险（尤其是吞吐与 smoke200 gate）。

---

### Task 1: 建立隔离工作区 + 基线测试（No-GPU）

**Files:**
- (no code yet)

**Step 1: 新建 worktree**

Run：
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260226-v2-nogpu-tools origin/main
cd .worktrees/owner-b-20260226-v2-nogpu-tools
```

**Step 2: 跑最小脚本测试集合**

Run：
```bash
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected：全部 PASS。

---

### Task 2: 统一吞吐统计输出（baseline 与 v2 同口径）

背景：当前 v2 runner 会写 `stats/throughput.json`，但 baseline runner 不写；导致“≤2x”止损线和复现证据链容易漂。

**Files:**
- Create: `scripts/write_throughput_json.py`
- Modify: `scripts/run_train_baseline_selfcap.sh`
- Modify: `scripts/run_train_feature_loss_v2_selfcap.sh`（可选：改为调用公共脚本，去掉内联 python）
- Test: `scripts/tests/test_write_throughput_json.py`

**Step 1: 先写失败测试（红灯）**

创建测试：`scripts/tests/test_write_throughput_json.py`

测试要点：
- 临时目录创建 `stats/train_step0199.json`（包含 `ellipse_time`）
- 运行 `python3 scripts/write_throughput_json.py <result_dir>`
- 断言 `stats/throughput.json` 存在且字段齐全（`step/elapsed_sec/iter_per_sec/source_stats`）

**Step 2: 跑测试确认 FAIL**

Run：
```bash
python3 scripts/tests/test_write_throughput_json.py
```

Expected：FAIL（脚本不存在或未写 throughput）。

**Step 3: 实现 `scripts/write_throughput_json.py`（最小实现）**

要求：
- 扫描 `<result_dir>/stats/train_step*.json`，取 step 最大的那个
- 解析 `ellipse_time`（若不存在则报错）
- 写入 `<result_dir>/stats/throughput.json`（schema 与 v2 runner 当前一致）

**Step 4: 复跑测试确认 PASS**

Run：
```bash
python3 scripts/tests/test_write_throughput_json.py
```

Expected：PASS。

**Step 5: baseline runner 接入**

在 `scripts/run_train_baseline_selfcap.sh` 末尾加入：
```bash
python3 scripts/write_throughput_json.py "$RESULT_DIR"
```

注意：该调用不改变训练过程，只补充统计文件。

**Step 6（可选但推荐）: v2 runner 也改用公共脚本**

把 `scripts/run_train_feature_loss_v2_selfcap.sh` 末尾内联 python 替换为：
```bash
python3 scripts/write_throughput_json.py "$RESULT_DIR"
```

**Step 7: 全量脚本测试回归**

Run：
```bash
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected：全部 PASS。

**Step 8: Commit**

```bash
git add scripts/write_throughput_json.py scripts/run_train_baseline_selfcap.sh scripts/run_train_feature_loss_v2_selfcap.sh scripts/tests/test_write_throughput_json.py
git commit -m "chore(stats): standardize throughput.json generation for runners"
```

---

### Task 3: evidence pack 纳入吞吐统计（便于审计 stoploss）

背景：`scripts/pack_evidence.py` 目前不收录 `stats/throughput.json`，导致“2x 以内”的证据链不完整。

**Files:**
- Modify: `scripts/pack_evidence.py`
- Modify: `scripts/tests/test_pack_evidence.py`

**Step 1: 先改测试（红灯）**

在 `scripts/tests/test_pack_evidence.py` 的临时 outputs/runA 下新增：
- `outputs/runA/stats/throughput.json`

并把它加入 `must_have` 断言集合。

**Step 2: 跑测试确认 FAIL**

Run：
```bash
python3 scripts/tests/test_pack_evidence.py
```

Expected：FAIL（tar 中缺 throughput.json）。

**Step 3: 修改 `scripts/pack_evidence.py` 收录 throughput.json**

实现建议：
- 在 `collect_files()` 中加入：
  - `outputs.glob("**/stats/throughput.json")`

注意：
- 不要收录 `ckpts/`、`tb/`、`renders/`（保持 tar 轻量）。

**Step 4: 复跑测试确认 PASS**

Run：
```bash
python3 scripts/tests/test_pack_evidence.py
```

Expected：PASS。

**Step 5: Commit**

```bash
git add scripts/pack_evidence.py scripts/tests/test_pack_evidence.py
git commit -m "chore(evidence): include stats/throughput.json in report packs"
```

---

### Task 4: Gate M1（smoke200）自动对比与 Pareto 输出（No-GPU）

目标：A 跑完 smoke200（含 lambda sweep）后，B 提供一条命令生成：
- smoke200 scoreboard（相对 baseline_smoke200 的 ΔPSNR/ΔLPIPS/ΔtLPIPS）
- Pareto（PSNR vs tLPIPS）与 knee point 建议（基于阈值约束）

**Files:**
- Create: `scripts/analyze_smoke200_m1.py`
- Test: `scripts/tests/test_analyze_smoke200_m1.py`
- Modify (docs): `docs/execution/2026-02-26-feature-loss-v2.md`

**Step 1: 写失败测试（红灯）**

测试策略：
- 生成一个临时 `metrics.csv`（只含少量行：baseline_smoke200 + 2 个 v2 smoke + 2 个 lam sweep）
- 运行脚本输出到临时 `out_md`
- 断言：
  - md 中包含表格 header
  - delta 计算正确
  - Pareto/frontier 行数符合预期（非支配解）
  - 推荐的 `knee`（或 best-under-threshold）符合预期

**Step 2: 跑测试确认 FAIL**

Run：
```bash
python3 scripts/tests/test_analyze_smoke200_m1.py
```

Expected：FAIL（脚本缺失）。

**Step 3: 实现 `scripts/analyze_smoke200_m1.py`**

CLI 建议：
- `--metrics_csv`（默认 `outputs/report_pack/metrics.csv`）
- `--out_md`（默认 `outputs/report_pack/scoreboard_smoke200.md`）
- `--step`（默认 199）
- `--stage`（默认 test）
- `--select_prefix`（默认 `outputs/protocol_v1/`）
- `--select_contains`（默认 `selfcap_bar_8cam60f`）
- `--baseline_regex`（默认 `^baseline_smoke200`）
- `--psnr_drop_max`（默认 0.5，用于“不过分退化”筛选）
- `--tlpips_rise_max`（默认 0.01）
- `--emit_json`（可选：输出 machine-readable 结果，供后续 pack）

输出 md 至少包含：
- “M1 table”：所有 smoke200 runs（按 run_name 排序）+ deltas vs baseline_smoke200
- “Pareto frontier”：对 (maximize PSNR, minimize tLPIPS) 的非支配点列表
- “Recommendation”：在 `PSNR >= baseline - psnr_drop_max` 且 `tLPIPS <= baseline + tlpips_rise_max` 下的最佳点（若无则明确说明）

**Step 4: 复跑测试确认 PASS**

Run：
```bash
python3 scripts/tests/test_analyze_smoke200_m1.py
```

Expected：PASS。

**Step 5: 更新执行文档（给 A 用）**

在 `docs/execution/2026-02-26-feature-loss-v2.md` 加入一段：
```bash
python3 scripts/analyze_smoke200_m1.py
```

并说明其输出路径与如何解读（不改协议）。

**Step 6: Commit**

```bash
git add scripts/analyze_smoke200_m1.py scripts/tests/test_analyze_smoke200_m1.py docs/execution/2026-02-26-feature-loss-v2.md
git commit -m "feat(analysis): add smoke200 M1 scoreboard + pareto helper"
```

---

### Task 5: Push + 交接给 A（不占 GPU）

**Step 1: 全量测试**

Run：
```bash
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected：全部 PASS。

**Step 2: Push**

Run：
```bash
git push origin HEAD:main
```

**Step 3: 交接口径（发给 A）**

给 A 的最短使用命令：
```bash
# smoke200 对比 + Pareto（A 跑完 M1 sweep 后执行）
python3 scripts/analyze_smoke200_m1.py
```

以及说明：
- baseline/v2/v2_gated 现在都会写 `stats/throughput.json`
- evidence pack 会包含吞吐统计，止损审计可复现

