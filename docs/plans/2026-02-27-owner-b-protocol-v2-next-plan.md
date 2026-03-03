# Owner B（No‑GPU）Protocol v2 Next Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 A 持续跑 GPU（`protocol_v2`）的同时，B 侧（No‑GPU）负责把新增 run 以“填空式”方式纳入同一条证据链：刷新 metrics/scoreboard、更新 report-pack 索引与 Q&A、重打离线证据包，并把 gate/止损结论写成可答辩口径。

**Architecture:** B 侧不做任何 GPU 训练，只做 4 件事：
1) **Intake**：核对 A 新 run 的“最小可审计产物”（cfg.yml + stats + 视频/可解释材料）。  
2) **Scoreboard**：刷新 `outputs/report_pack/metrics.csv` 并生成 v2/cross-protocol 的表。  
3) **Packaging**：重打 `scripts/pack_evidence.py` 的 tarball + manifest 快照。  
4) **Narrative**：把 gate/止损与失败机理写回 `docs/report_pack/` + `4D-Reconstruction-v2.md` + `notes/qna.md`。

**Tech Stack:** Markdown、Python（`scripts/build_report_pack.py` / `scripts/summarize_scoreboard.py` / `scripts/pack_evidence.py`）、tar/sha256、pytest（`scripts/tests`）。

---

## Task 0: Preflight（No‑GPU 环境与不变量）

**Files:**
- Read: `docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- Read: `docs/protocols/protocol_v2.yaml`
- Read: `docs/report_pack/2026-02-27-v2/README.md`
- Read: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`

**Step 1: 口径核对（不变量）**
- 阶段一证据链：`v26 + protocol_v1` 不动，只引用、不改动结论。  
- 阶段二新增：所有新实验与新结论必须在 `outputs/protocol_v2/...`，并在 v2 report-pack 中落盘。

**Step 2: 跑一次单测，保证后续刷新不会引入回归**

Run: `pytest -q scripts/tests`  
Expected: PASS

---

## Task 1: A 新 run Intake Checklist（收到结果后 10 分钟内完成）

**Files:**
- Update: `docs/report_pack/2026-02-27-v2/README.md`
- Update: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`（仅在结论发生变化时）

**Step 1: 对每个 A 新的 RESULT_TAG，检查“最小可审计”文件是否齐全**

对任一新目录 `outputs/protocol_v2/selfcap_bar_8cam60f/<RESULT_TAG>/`，至少要求：
- `cfg.yml`（真源配置）
- `stats/test_step0199.json`（smoke200）或 `stats/test_step0599.json`（full600）
- `videos/traj_4d_step*.mp4`（可选但强建议，用于快速定性 sanity）

Expected: 缺任何一项→直接回 A 补齐（不要让 scoreboard 里出现“无 cfg 的结论”）。

**Step 2: 把新 run 路径补到 report-pack README 的“产物回填状态”清单**
- 只写路径与一句话结论（通过 gate / 未通过 gate / 触发止损）。

---

## Task 2: 刷新 report-pack（metrics.csv）并生成 scoreboard（每次 Intake 后执行）

**Files:**
- Update: `outputs/report_pack/metrics.csv`（由脚本生成）
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard.md`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

**Step 1: 刷新 metrics.csv**

Run: `python3 scripts/build_report_pack.py`  
Expected: `outputs/report_pack/metrics.csv` 新增/更新 A 的 run 行（按 run_dir + step）。

**Step 2: 生成 v2-only smoke200 scoreboard（step=199）**

Run:
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --stage test \
  --step 199
```
Expected: 表中出现新增 `planb_feat_v2_smoke200_*` 行。

**Step 3: 生成 v2-only full600 scoreboard（step=599）**

Run:
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --stage test \
  --step 599
```

**Step 4: 生成 cross-protocol full600 对比（v1 vs v2，含 Δ）**

Run:
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix '' \
  --stage test \
  --step 599
```

**Step 5: 快速判断是否触发止损（只看 planb_init_600 vs 新 full600）**
- 若 `scoreboard_full600_vs_v1.md` 显示新 full600 相对 `planb_init_600` 命中 **PSNR↓ / LPIPS↑ / tLPIPS↑**：在 README 写“止损触发，停止 sweep”，并引用 A 的审计 note。

---

## Task 3: 重打离线证据包（tarball + manifest 快照）

**Files:**
- Update: `outputs/report_pack_2026-02-27.tar.gz`（或按当日生成新文件）
- Update: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- Update: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: 生成/覆盖 tarball**

Run: `python3 scripts/pack_evidence.py`  
Expected: 输出提示写入 `outputs/report_pack_2026-02-27.tar.gz`（并包含 `manifest_sha256.csv`）。

**Step 2: 把 tar 内 manifest 解包为 repo 快照（source-of-truth=tar 内）**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-27.tar.gz manifest_sha256.csv \
  > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```

**Step 3: 在 report-pack README 更新“tarball 路径 + 核对方法”**
- 若 tarball 名称/日期变化，必须同步写清楚。

---

## Task 4: Narrative 收口（答辩口径随 A 的结论更新）

**Files:**
- Update: `4D-Reconstruction-v2.md`
- Update: `notes/qna.md`
- (Optional) Update: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`

**Step 1: 若 A 找到“非全线劣化”的设置**
- 在 `4D-Reconstruction-v2.md` 的 “protocol_v2 产物落盘与回填” 段追加新 run 路径与一句话结论（不写夸大承诺）。
- 在 `notes/qna.md` 更新“stage‑2 止损/趋势”问答（从“止损”变成“通过 gate 的最小正趋势”）。

**Step 2: 若 A 仍无趋势（持续 gate fail）**
- 把结论固化为“负结果 + 失败机理 + 未来工作”，并在 report-pack README 明确：`protocol_v2` 的价值是“补齐承诺与可解释材料”，不是强行追指标。

---

## Done Criteria（B 侧交付完成的判据）

当 A 任意新增 run 后，B 能在 **同一天** 完成：
- `metrics.csv` 更新 + 3 份 scoreboard 更新（v2 smoke / v2 full / cross-protocol full）  
- tarball 重打 + `manifest_sha256.csv` 快照同步  
- report-pack README 与 Q&A 口径同步到最新 gate/止损结论

