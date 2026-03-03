# protocol_v2 C2(noconf) full600 Integration Plan (Owner B / No‑GPU)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 当 A（GPU0）按 `docs/plans/2026-02-28-owner-a-protocol-v2-c2-full600-budget-plan.md` 执行“预算闸门→（若获批）仅 1 次 C2(noconf) full600”时，B（No‑GPU）负责把新增产物以“填空式”方式纳入同一证据链：刷新 `metrics.csv/scoreboard`、更新 report-pack / 开题 v2 / Q&A / 验收记录，并重打离线证据包（tar + manifest 快照）。

**Architecture:** B 侧不做训练，只做 4 件事：
1) **Intake**：核对 A 新 run 的最小可审计产物（cfg + stats + 视频 + ckpt）。  
2) **Scoreboard**：刷新 `outputs/report_pack/metrics.csv` 并生成 3 份表（v2 smoke / v2 full / cross-protocol full）。  
3) **Packaging**：重打 tarball + 从 tar 内回填 `manifest_sha256.csv` 快照。  
4) **Narrative**：把“是否出现稳定性改善/是否仍为 trade-off/是否触发止损/是否继续申请预算”写成可答辩口径，并同步到所有入口文档。

**Tech Stack:** Python（`scripts/build_report_pack.py` / `scripts/summarize_scoreboard.py` / `scripts/pack_evidence.py`）、Markdown、tar/sha256、pytest（`scripts/tests`）。

---

## Task 0: Preflight（15 分钟）

**Files:**
- Read: `docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- Read: `docs/protocols/protocol_v2.yaml`

**Step 1: 跑单测，保证工具链稳定**

Run: `pytest -q scripts/tests`  
Expected: PASS

---

## Task 1: Intake（收到 A 的 handoff 后立即执行）

**Files:**
- Update: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: 判断 A 是否获得预算并实际跑了 full600**

检查是否存在：
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/`

Run:
```bash
ls -la outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf 2>/dev/null || true
```

**Step 2A: 若目录不存在（预算未批 / 未执行）**
- 在 `docs/report_pack/2026-02-27-v2/README.md` 的 stage‑2 段追加一句：本轮预算未批准，因此不新增 full600；以 smoke 趋势 + trade-off 定性证据收口。

**Step 2B: 若目录存在（预算已批 / 已执行）→ 做“最小可审计”检查**

必须齐全：
- `.../cfg.yml`
- `.../stats/test_step0599.json`
- `.../videos/traj_4d_step599.mp4`
- `.../ckpts/ckpt_599.pt`

Run:
```bash
RUN=outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf
ls -la $RUN/cfg.yml
ls -la $RUN/stats/test_step0599.json
ls -la $RUN/videos/traj_4d_step599.mp4
ls -la $RUN/ckpts/ckpt_599.pt
```
Expected: 全部存在；缺任一项→立刻回 A 补齐（不允许进入 scoreboard/叙事）。

---

## Task 2: 刷新 metrics + scoreboard（三表同日更新）

**Files:**
- Update: `outputs/report_pack/metrics.csv`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard.md`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

**Step 1: 刷新 metrics.csv**

Run: `python3 scripts/build_report_pack.py`  
Expected: 输出行数增加；新 full600（若存在）应出现在 `metrics.csv` 中（step=599, stage=test/val）。

**Step 2: 生成 v2-only smoke200（step=199）**

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

**Step 3: 生成 v2-only full600（step=599）**

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

**Step 4: 生成 cross-protocol full600（含 Δ）**

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

---

## Task 3: Narrative（把“C2 full600 是否有效”写成可答辩结论）

**Files:**
- Update: `docs/report_pack/2026-02-27-v2/README.md`
- Update: `4D-Reconstruction-v2.md`
- Update: `notes/qna.md`

**Step 1: 更新 report-pack README（最重要）**
- 若 `..._noconf full600` 存在：补齐路径 + 一句话结论（相对 `planb_init_600` 与相对 conf-on full600 的对比）。
- 若不存在：明确“预算未批/未执行”的收口口径。
- 始终保持克制：只写 mixed trend / trade-off / stoploss / budget discipline，不写“显著提升”。

**Step 2: 同步到开题 v2（阶段二结论收口段）**
- 在 `4D-Reconstruction-v2.md` 的“阶段二结论收口”更新一句：C2 full600（是否）验证结论。

**Step 3: 更新 Q&A（只补 2–3 行）**
- “是否最终批准新增 full600？为什么？”
- “C2(noconf) full600 的结论是什么？证据在哪里？”

---

## Task 4: Packaging（tarball + manifest 快照）

**Files:**
- Update: `outputs/report_pack_2026-02-28.tar.gz`
- Update: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- Update: `docs/report_pack/2026-02-27-v2/README.md`（如 tarball 路径变化）

**Step 1: 重打 tarball（建议固定 out_tar，避免日期漂移）**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
```

**Step 2: 从 tar 内回填 manifest 快照（source-of-truth=tar 内）**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv \
  > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```

**Step 3: 快速校验 tar 内包含新增 full600（若存在）与关键 mp4**

Run（full600）：
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/stats/test_step0599.json" || true
```

Run（side-by-side）：
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "outputs/qualitative/planb_vs_baseline/.*\\.mp4" | head
```

---

## Task 5: 验收记录增补（5 分钟）

**Files:**
- Update: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`

**Step 1: 若本轮新增了“预算 full600 验证”**
- 在文末追加一个小节：列出新增 run 路径 + stoploss 判定 + 一句话结论。
- 若预算未批：追加一句“未执行 full600，按纪律收口”的记录即可。

---

## Done Criteria（B 侧完成判据）

- `pytest -q scripts/tests` PASS
- `outputs/report_pack/metrics.csv` 已纳入最新产物（含可选的 `..._noconf full600`）
- 3 份 scoreboard 更新完成（v2 smoke / v2 full / cross full）
- `outputs/report_pack_2026-02-28.tar.gz` 重打 + `docs/report_pack/2026-02-27-v2/manifest_sha256.csv` 回填
- `docs/report_pack/2026-02-27-v2/README.md`、`4D-Reconstruction-v2.md`、`notes/qna.md`、`docs/reviews/2026-02-27/acceptance-2026-02-27.md` 口径同步

