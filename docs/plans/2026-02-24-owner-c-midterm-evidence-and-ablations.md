# Owner C Midterm Evidence + Ablations Plan (GPU2)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 midterm 需要的“可交付五件套”在主阵地固化为可复现证据与材料：Baseline 稳定长跑、关键 ablation（先基线敏感性，后接 weak/strong）、失败案例整理、以及一键离线证据包（含 hash manifest）。

**Scope 对齐：**本计划对应 `~/2026-02-12-4d-reconstruction-execution.md` 的 Task 11（证据打包）与 midterm 汇报准备。不会实现 cue mining / weak/strong 融合算法本体（由 A/B 负责）。

**Parallel Safety:** 不修改 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`，避免与 A 的 weak-fusion 改动冲突；主要改动集中在 `scripts/` 与 `notes/`。

**Default Resources:** C 使用 `GPU2` 跑 600-step baseline（可选再加 1 条对照），其余在 CPU 完成。

---

## Task C10: 创建隔离 Worktree/分支

**Files:**
- None (worktree only)

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-c-20260224-midterm-pack .worktrees/owner-c-20260224-midterm-pack main
cd .worktrees/owner-c-20260224-midterm-pack
git status --porcelain=v1
```

Expected:
- `status` 输出为空

---

## Task C11: 固化 midterm 实验矩阵与命名（先写清楚再跑）

**Files:**
- Create: `notes/midterm_exp_matrix.md`

要求（写到能直接照抄跑）：
- 统一数据入口：`data/selfcap_bar_8cam60f`
- 统一关键参数：`START_FRAME=0 END_FRAME=60 KEYFRAME_STEP=5 CONFIG=default_keyframe_small`
- 统一输出命名规则（建议）：
  - baseline 600-step：`outputs/gate1_selfcap_baseline_600`
  - baseline 对照（可选）：`outputs/gate1_selfcap_baseline_200_gs6` 等
  - weak/strong（等 A/B 合入后补）：`outputs/gate1_selfcap_ours_weak_600` / `outputs/gate1_selfcap_ours_strong_600`
- 明确“本轮必须产出”的最小集合：
  - 1 条 baseline 600-step 视频 + stats
  - 1 个离线证据包（含 manifest_sha256.csv）
  - 失败案例 2 条（截图或视频片段）

验收：
- 文档里包含至少 3 条可直接执行的命令块（baseline、report_pack、pack_evidence）

---

## Task C12: GPU2 跑 baseline 600-step（SelfCap bar 8cam60f）

**Files:**
- Create (runtime only): `outputs/gate1_selfcap_baseline_600/*`

Run:
```bash
cd /root/projects/4d-recon
MAX_STEPS=600 EVAL_STEPS=600 SAVE_STEPS=600 RENDER_TRAJ_PATH=fixed \
bash third_party/FreeTimeGsVanilla/run_pipeline.sh \
  data/selfcap_bar_8cam60f/triangulation data/selfcap_bar_8cam60f \
  outputs/gate1_selfcap_baseline_600 0 60 5 2 default_keyframe_small
```

Expected:
- `outputs/gate1_selfcap_baseline_600/videos/traj_4d_step599.mp4`
- `outputs/gate1_selfcap_baseline_600/stats/val_step0599.json`

---

## Task C13: report-pack 刷新与表格化输出（不改训练代码）

**Files:**
- (Optional) Modify: `scripts/build_report_pack.py`（只做增量增强，默认行为不变）
- (Optional) Create: `scripts/render_metrics_table.py`
- Update: `outputs/report_pack/ablation_notes.md`
- Update: `outputs/report_pack/failure_cases.md`

最低要求（不写代码也可完成）：
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

建议增强（可选，二选一即可）：
- A) `build_report_pack.py` 增加 `--pick {latest,best_psnr}`，默认 `latest`；用于 sweep 时自动取 best。
- B) 新增 `scripts/render_metrics_table.py`：把 `outputs/report_pack/metrics.csv` 转成 `table_metrics.md`（按 gate/dataset 排序，便于直接贴进 slides）。

验收：
- `outputs/report_pack/metrics.csv` 包含 `gate1_selfcap_baseline_600` 的一行
- `ablation_notes.md` 写明目前已有对照、缺口（weak/strong 待补）与下一步

---

## Task C14: 失败案例与机制解释（可直接用于答辩 Q&A）

**Files:**
- Update: `outputs/report_pack/failure_cases.md`
- (Optional) Create: `outputs/report_pack/failure_viz/`（截图/短视频片段，产物不入库也可）

要求：
- 至少 2 条 failure case（优先选“遮挡/快速运动/背景少纹理”场景现象）：
  - 现象描述（1-2 句）
  - 可能机制（对应到 pipeline：triangulation 稀疏、keyframe gap、线性运动假设、时间归一化、mask/对应误差）
  - 可复现指令（指向对应 `outputs/...`）
  - 截图/视频路径（1 个即可）

验收：
- `failure_cases.md` 至少新增 2 个小节（标题 + 路径 + 机制解释）

---

## Task C15: 离线证据包 v2（含 sha256 manifest）

**Files:**
- Create (runtime only): `outputs/*midterm*.tar.gz`
- (Optional) Update: `notes/demo-runbook.md`

Run（示例）：
```bash
cd /root/projects/4d-recon
python3 scripts/pack_evidence.py \
  --outputs_root outputs \
  --out_tar outputs/midterm_evidence_2026-02-24.tar.gz
```

Expected:
- tar 内含 `outputs/report_pack/metrics.csv`
- tar 内含 `manifest_sha256.csv`，且脚本校验 PASS（若脚本支持自检）

---

## Task C16 (可选，等 A/B 合入后补跑): weak/strong 对比与最终表格落地

**说明：**等 A 的 weak-fusion 与 B 的 correspondence 产物/设计落地后，本任务再执行（避免反复重跑浪费 GPU）。

交付：
- baseline vs ours-weak vs ours-strong 的三条视频（同场景同 seed 同步）
- `metrics.csv`/`table_metrics.md` 更新为三行对比
- `ablation_notes.md` 补齐结论（弱融合有效性、强融合是否改善 flicker/一致性）

