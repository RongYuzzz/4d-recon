# Owner A Midterm Pack v12 + Doc Refresh Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在只剩 A/B 两人（GPU0/GPU1）的情况下，由 A 接管“汇报材料主线”，把主阵地文档与证据链更新到可直接用于中期汇报的 **v12**（含 strong v3 / VGGT probe 的可审计记录）。

**Architecture:** A 不碰训练器主逻辑（避免与 B 冲突），只做“结果收敛 + 文档口径一致 + 证据包可复现”。核心动作是把分散在 worktree 的关键产物（只保留 `stats/`+`videos/`+`cfg.yml`+`keyframes*.npz`）同步到主阵地 `outputs/`，再刷新 `outputs/report_pack/`、打包 evidence tarball、落地 `docs/report_pack/` 快照并更新 `Progress.md` 与 runbook。

**Tech Stack:** bash、git、rsync、Python（`scripts/build_report_pack.py` / `scripts/pack_evidence.py` / `scripts/summarize_scoreboard.py`）。

---

### Task 1: Create Owner-A Worktree For v12

**Files:**
- Create: `docs/plans/2026-02-25-owner-a-midterm-pack-v12-and-doc-refresh.md`

**Step 1: Create worktree**

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260225-pack-v12 .worktrees/owner-a-20260225-pack-v12 main
git -C .worktrees/owner-a-20260225-pack-v12 status --porcelain=v1
```

Expected: worktree 干净（无输出）。

**Step 2: Commit this plan doc**

Run:
```bash
cd /root/projects/4d-recon
git add docs/plans/2026-02-25-owner-a-midterm-pack-v12-and-doc-refresh.md
git commit -m "docs(plans): add owner-a v12 midterm pack and doc refresh plan"
```

Expected: commit 成功。

---

### Task 2: Sync A 的 VGGT Probe 产物到主阵地 outputs（只同步轻量文件）

**Files:**
- Modify (local only, gitignored): `outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/*`
- Modify (local only, gitignored): `outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/*`

**Step 1: 同步 cue_mining/vggt_probe（含 pseudo_masks + quality + viz）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12

SRC=/root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt/outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/
DST=outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/
mkdir -p "$DST"
rsync -a "$SRC" "$DST"
test -f "$DST/pseudo_masks.npz"
test -f "$DST/quality.json"
test -f "$DST/viz/overlay_cam02_frame000000.jpg"
```

Expected: 3 个 `test -f` 全部通过。

**Step 2: 同步 weak_vggt probe run（排除 renders/tb/ckpts）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12

for run in ours_weak_vggt_w0.3_end200_s200 ours_weak_vggt_w0.3_end200_600; do
  SRC=/root/projects/4d-recon/.worktrees/owner-a-20260225-pack-and-weak-vggt/outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/${run}/
  DST=outputs/exp_weak_vggt_probe/selfcap_bar_8cam60f/${run}/
  mkdir -p "$DST"
  rsync -a --exclude 'renders' --exclude 'tb' --exclude 'ckpts' "$SRC" "$DST"
  test -f "$DST/stats/test_step0199.json" || true
  test -f "$DST/stats/test_step0599.json" || true
  ls -la "$DST/stats" | head
  ls -la "$DST/videos" | head
done
```

Expected:
- 两个 run 的 `stats/` 与 `videos/` 都存在且非空。

---

### Task 3: Sync B 的 strong v3 full600 轻量产物到主阵地 outputs（若尚未同步）

**Files:**
- Modify (local only, gitignored): `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/*`

**Step 1: rsync（排除 renders/tb/ckpts）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12

SRC=/root/projects/4d-recon/.worktrees/owner-b-20260225-strong-v3/outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/
DST=outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/
mkdir -p "$DST"
rsync -a --exclude 'renders' --exclude 'tb' --exclude 'ckpts' "$SRC" "$DST"
test -f "$DST/stats/test_step0599.json"
test -f "$DST/videos/traj_4d_step599.mp4"
```

Expected: 两个 `test -f` 通过。

---

### Task 4: 更新汇报用文本（outputs/report_pack）以匹配 v11 现状（避免 tar 内文档互相打架）

**Files:**
- Modify (local only, gitignored): `outputs/report_pack/ablation_notes.md`
- Modify (local only, gitignored): `outputs/report_pack/failure_cases.md`

**Step 1: 更新 ablation_notes（补齐 strong v3 / VGGT probe / feature-loss 止损）**

编辑要求（写进文件即可）：
- 标题日期改为 `2026-02-25`，并注明“当前由 A/B 维护（C 暂不可用）”
- 增加条目：
  - `ours_strong_v3_gate1_detach0_predpred_600`（引用 `notes/ours_strong_v3_gated_attempt.md` 的止损结论）
  - `ours_weak_vggt_w0.3_end200_600`（标注为 `outputs/exp_weak_vggt_probe/...`，结论：不建议开 protocol_v2）
  - feature-loss v1（引用 `notes/feature_loss_v1_attempt.md`，结论：止损）

**Step 2: 更新 failure_cases（新增 strong v3 与 vggt probe 的“为何无收益”案例）**

编辑要求：
- 新增 2 个 case（每个 6-10 行即可）：
  - Case: strong v3（tLPIPS 小幅下降但 LPIPS/PSNR 退化，属于 trade-off，未达成功线）
  - Case: VGGT cue（cue 不退化但 temporal flicker 指标偏高，weak 注入不带来收益）

**Step 3: 校验文件存在**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
rg -n "strong_v3|vggt_probe|feature_loss" outputs/report_pack/ablation_notes.md
rg -n "strong v3|VGGT|vggt" outputs/report_pack/failure_cases.md
```

Expected: 两个 `rg` 都能命中新增段落。

---

### Task 5: 更新主阵地可复现指引（demo-runbook + Progress）

**Files:**
- Modify: `notes/demo-runbook.md`
- Modify: `Progress.md`

**Step 1: 更新 runbook GPU 编号（去掉 GPU2）**

在 `notes/demo-runbook.md`：
- 将所有 `GPU=2` / `CUDA_VISIBLE_DEVICES=2` 改为 `GPU=0`（baseline/weak/control）与 `GPU=1`（strong 相关），并注明“单机两卡假设”。
- “Pack evidence” 命令改为写入 `artifacts/report_packs/`，并提醒 `SHA256SUMS.txt` 登记。
- 增加 strong v3 的播放路径（只列一行即可）：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/ours_strong_v3_gate1_detach0_predpred_600/videos/traj_4d_step599.mp4`

**Step 2: 更新 Progress.md（引用 v11/v12，补齐 strong v3 与 vggt probe 结论）**

在 `Progress.md`：
- “最后更新日期”改为 `2026-02-25`
- “当前结果摘要”来源改为最新快照（本计划产出的 v12 或现有 v11）
- 在“当前待办”里明确：
  - weak 主线风险：`control_weak_nocue_600` 仍优于 `ours_weak_600`
  - strong 已按 stoploss 冻结（v3 亦止损）
  - 下一步由 B 主导“weak 的更合理 cue/注入”或“更强但可解释的 strong”探索（引用对应 plan）

**Step 3: 最小一致性检查**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected: 全部 PASS。

---

### Task 6: 刷新 report-pack + evidence v12，并提交快照（tar.gz 不入库）

**Files:**
- Modify: `artifacts/report_packs/SHA256SUMS.txt`
- Create: `docs/report_pack/2026-02-25-v12/*`

**Step 1: 刷新 report-pack（metrics/scoreboard）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv > outputs/report_pack/scoreboard.md
rg -n "ours_strong_v3_gate1_detach0_predpred_600" outputs/report_pack/scoreboard.md
```

Expected: `rg` 命中 strong v3 一行。

**Step 2: 打包 evidence tar（v12）并登记 sha256**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
DATE_TAG="2026-02-25-v12"
OUT_TAR="artifacts/report_packs/report_pack_${DATE_TAG}.tar.gz"
python3 scripts/pack_evidence.py --repo_root . --out_tar "$OUT_TAR"
sha256sum "$OUT_TAR" | tee -a artifacts/report_packs/SHA256SUMS.txt
```

Expected:
- tar.gz 非空
- `SHA256SUMS.txt` 追加 1 行（v12）

**Step 3: 落地 docs 快照目录（v12）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
SNAP_DIR="docs/report_pack/${DATE_TAG}"
mkdir -p "$SNAP_DIR"
cp -f outputs/report_pack/metrics.csv "$SNAP_DIR/metrics.csv"
cp -f outputs/report_pack/scoreboard.md "$SNAP_DIR/scoreboard.md"
cp -f outputs/report_pack/ablation_notes.md "$SNAP_DIR/ablation_notes.md"
cp -f outputs/report_pack/failure_cases.md "$SNAP_DIR/failure_cases.md"
tar -xOzf "$OUT_TAR" manifest_sha256.csv > "$SNAP_DIR/manifest_sha256.csv"
ls -la "$SNAP_DIR"
```

Expected: v12 快照 5 个文件齐全。

**Step 4: Commit（只提交文本快照与 sha 清单，不提交 tar.gz）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
git add artifacts/report_packs/SHA256SUMS.txt Progress.md notes/demo-runbook.md docs/report_pack/2026-02-25-v12
git commit -m "docs(report-pack): snapshot v12 and refresh runbook/progress"
```

Expected: commit 成功。

**Step 5: Push**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-pack-v12
git push origin HEAD:main
```

Expected: push 成功（fast-forward）。

