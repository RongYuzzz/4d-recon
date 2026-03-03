# protocol_v2 Stage‑2 Trade-off Integration (Owner B / No‑GPU) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 A（GPU0）执行 stage‑2 trade‑off 诊断（定性证据 + ≤2 次 smoke200）期间，B（No‑GPU）把所有新增产物以“填空式”方式纳入同一条证据链：刷新 `metrics.csv/scoreboard`、更新 report-pack 叙事与 Q&A、重打离线证据包并同步 `manifest_sha256.csv` 快照。

**Architecture:** B 侧不做任何训练；只做 4 件事：1) Intake（最小可审计产物检查）2) Scoreboard（metrics + 三表）3) Packaging（tarball + manifest 快照）4) Narrative（README + 开题 v2 + Q&A + 验收记录）。

**Tech Stack:** Markdown、Python（`scripts/build_report_pack.py` / `scripts/summarize_scoreboard.py` / `scripts/pack_evidence.py`）、tar/sha256、pytest（`scripts/tests`）、shell 工具（`ls` / `tar` / `rg`）。

---

### Task 0: Preflight（15 分钟）

**Files:**
- Read: `docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- Read: `docs/protocols/protocol_v2.yaml`
- Read: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: 确认不变量（只做一次）**
- `v26 + protocol_v1` 证据链冻结不动（只引用不改口径）。
- 所有新增实验/导出/定性证据统一落 `protocol_v2` 或 `outputs/qualitative/`（避免把 v1 表格污染）。

**Step 2: 跑单测保证脚本工具链稳定**

Run: `pytest -q scripts/tests`  
Expected: PASS

---

### Task 1: Intake A 的新增产物（每次 A drop 后 10 分钟内完成）

**Files:**
- Update: `docs/report_pack/2026-02-27-v2/README.md`
- (Optional) Update: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`（仅当结论有新增/变化）

**Step 1: 列出 A 本轮“应交付”的新增条目（按目录为单位）**

最低要求（缺任一项直接回 A 补齐，不进入 scoreboard）：
- 新 smoke run：`outputs/protocol_v2/selfcap_bar_8cam60f/<RESULT_TAG>/{cfg.yml,stats/test_step0199.json,videos/traj_*.mp4}`
- 新 export-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_*_tau*/videos/traj_4d_step599.mp4`
- 定性对比：`outputs/qualitative/planb_vs_baseline/*.mp4`
- 解释性口径：`notes/*.md`（A 的审计 note 与 trade-off note）

Run（示例，按实际 RESULT_TAG 替换/增删）：
```bash
ls -la outputs/qualitative/planb_vs_baseline || true
ls -la outputs/protocol_v2/selfcap_bar_8cam60f | rg -n "planb_feat_v2_smoke200|export_planbfeat|export_planb_"
```
Expected: 能看到新增目录名与视频文件存在。

**Step 2: 在 report-pack README 的“产物回填状态”段补齐路径 + 一句话结论**
- 每个新增 run 只写：路径 + gate/止损状态 + 1 句解释（不要扩大战果）。

---

### Task 2: 刷新 `metrics.csv` + 三份 scoreboard（每次 Intake 后执行）

**Files:**
- Update: `outputs/report_pack/metrics.csv`（脚本生成）
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard.md`
- Update: `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

**Step 1: 刷新 metrics**

Run: `python3 scripts/build_report_pack.py`  
Expected: `outputs/report_pack/metrics.csv` 行数增加/更新（包含 A 新 run 的 step=199/599）。

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
Expected: 表格出现新增 `planb_feat_v2_smoke200_*` 行。

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

**Step 4: 生成 cross-protocol full600 对比（含 Δ）**

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

**Step 5: 把“trade-off”用一句话固化到 report-pack README**
- 若 cross 表显示 `PSNR↑` 但 `LPIPS/tLPIPS↑`：在 README 的 stage‑2 段写明这是 trade‑off，不是稳定增益，并引用 A 的审计 note 与定性视频路径。

---

### Task 3: Narrative（把“能答辩的话术”同步到 3 个入口）

**Files:**
- Update: `docs/report_pack/2026-02-27-v2/README.md`
- Update: `4D-Reconstruction-v2.md`
- Update: `notes/qna.md`

**Step 1: 在 report-pack README 增加/更新“Stage‑2 trade‑off diagnosis”小节**
必须包含：
- 3 个 side‑by‑side 视频路径（baseline vs planb；planb vs planb+feat；baseline vs planb+feat）
- `planb_init_600` 与 `planb_feat_v2_full600_*` 的动静解耦视频路径（若 A 已导出）
- 结论一句话：当前为混合趋势（PSNR↑但稳定性未改善），遵守预算纪律不新增 full600 sweep

**Step 2: 在 `4D-Reconstruction-v2.md` 同步“阶段二结论收口”**
- 保持克制：写“证据链补齐 + 混合趋势 + 失败机理假设/未来工作”，不要写“显著提升”。

**Step 3: 更新 `notes/qna.md` 的必问点**
至少补齐（每条 2–4 行）：
- 为什么会出现 `PSNR↑` 但 `tLPIPS↑`（画面上是什么现象？）
- 为什么这时候不继续 sweep full600（预算纪律/止损线）
- 证据指针（scoreboard + side‑by‑side + export-only）

---

### Task 4: 重打离线证据包（同日完成）

**Files:**
- Update: `outputs/report_pack_2026-02-27.tar.gz`
- Update: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- Update: `docs/report_pack/2026-02-27-v2/README.md`（如路径/核对方法有变化）

**Step 1: 生成/覆盖 tarball**

Run: `python3 scripts/pack_evidence.py`  
Expected: 写入 `outputs/report_pack_2026-02-27.tar.gz`。

**Step 2: 用 tar 内 manifest 回填 repo 快照（source-of-truth=tar 内）**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-27.tar.gz manifest_sha256.csv \
  > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```

**Step 3: 快速验证 tarball 确实包含新增定性证据（至少命中一条）**

Run:
```bash
tar -tzf outputs/report_pack_2026-02-27.tar.gz | rg -n "outputs/qualitative/planb_vs_baseline/.*\\.mp4" || true
```
Expected: 能 grep 到至少一个 side‑by‑side mp4 路径。

---

### Task 5: 验收记录（可选但推荐，5 分钟）

**Files:**
- (Optional) Update: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`

**Step 1: 若结论有新增（例如新增 smoke 候选通过 gate / 新增 trade-off 定性证据）**
- 在验收记录末尾追加一个“增补验收”小段：列出新增产物路径 + 结论一句话。

---

### Done Criteria（B 侧完成判据）

当 A 任意新增产物后，B 能在 **同一天** 完成：
- `metrics.csv` 更新 + 3 份 scoreboard 更新
- tarball 重打 + `manifest_sha256.csv` 快照同步
- `docs/report_pack/2026-02-27-v2/README.md`、`4D-Reconstruction-v2.md`、`notes/qna.md` 口径与证据指针同步

