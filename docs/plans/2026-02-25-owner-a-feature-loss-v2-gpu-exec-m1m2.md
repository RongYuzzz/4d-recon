# Owner A: Feature-Loss v2 GPU Execution + Evidence Refresh (M1/M2) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `protocol_v1` 不变的前提下，用 GPU0 完成 feature-loss v2 的 M1(200-step) 与 M2(full600) 关键实验，并把结果固化进 report-pack/evidence（文本快照 + sha）。

**Architecture:** A 负责 GPU 执行与证据链刷新；B 负责不依赖 GPU 的 v2 代码落地（runner/sanity/cache/flags 等）。A 的执行严格按 `docs/execution/2026-02-26-feature-loss-v2.md` 的 Gate 约束：先 M1 再 M2，full600 最多两次。

**Tech Stack:** Bash（runner）、Python（report-pack/evidence 脚本）、PyTorch/CUDA（训练）、VGGT（冻结推理）、FreeTimeGsVanilla trainer。

---

### Task A1: 建立隔离执行环境 + 预检（不占用长 GPU 时间）

**Files:**
- Create: `notes/v2_m1_preflight_owner_a.md`

**Step 1: 创建隔离 worktree（避免污染 main）**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260225-v2-gpu-exec origin/main
cd .worktrees/owner-a-20260225-v2-gpu-exec
```
Expected: worktree 创建成功，`git status` 干净。

**Step 2: 校验 canonical 数据目录契约**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
ls -la data/selfcap_bar_8cam60f
ls -la data/selfcap_bar_8cam60f/images | head
ls -la data/selfcap_bar_8cam60f/triangulation | head
ls -la data/selfcap_bar_8cam60f/sparse/0
```
Expected:
- `images/02..09/000000.jpg` 等存在
- `triangulation/points3d_frame000000.npy` 等存在（至少 60 帧）
- `sparse/0/{cameras.bin,images.bin,points3D.bin}` 存在

**Step 3: 校验训练 venv / VGGT 依赖可用（短检查）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
VENV_PYTHON=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
"$VENV_PYTHON" -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; print('VGGT import OK')"
```
Expected: 输出 `cuda True`（若当前 GPU0 可用）且 `VGGT import OK`。

**Step 4: 记录预检结果**

Edit `notes/v2_m1_preflight_owner_a.md`，写入：
- 当前日期时间
- `DATA_DIR=data/selfcap_bar_8cam60f` 契约检查结果
- venv/python/torch/vggt import 结果

**Step 5: 提交（仅提交文本，不提交 outputs/artifacts）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
git add notes/v2_m1_preflight_owner_a.md
git commit -m "notes: v2 M1 preflight checklist (owner a)"
```
Expected: commit 成功。

---

### Task A2: 等待 B 合入 v2 runner/sanity 后，执行 Gate M1（200-step）

**Files:**
- Modify: `notes/v2_m1_preflight_owner_a.md`
- Create: `notes/v2_m1_results_owner_a.md`

**Step 1: 同步到最新 main（拿到 B 的 v2 代码）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
git pull --ff-only origin main
```
Expected: fast-forward 成功（若失败，立刻停下协调）。

**Step 2: 运行 v2 sanity（预处理一致性与 cache round-trip）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
python3 scripts/check_vggt_preprocess_consistency.py --help
```
Expected: 脚本存在且能打印帮助信息。

随后按 B 的实现参数执行（以脚本帮助为准），预期输出 PASS（或明确的 FAIL 原因）。

**Step 3: 启动 200-step v2（GPU0）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
GPU=0 MAX_STEPS=200 RESULT_TAG=feature_loss_v2_smoke200 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```
Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_smoke200/stats/test_step0199.json` 存在
- `.../videos/traj_4d_step199.mp4` 存在
- 若有 `throughput.json` 或吞吐字段，需存在并可读

**Step 4: 启动 200-step v2_gated（GPU0）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
GPU=0 MAX_STEPS=200 RESULT_TAG=feature_loss_v2_gated_smoke200 \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```
Expected: 同上，产物齐全。

**Step 5: M1 止损判定（只看是否“灾难性退化/吞吐失控”）**

操作：
- 把两个 run 的 PSNR/LPIPS/tLPIPS 与 `baseline_600`、`control_weak_nocue_600` 做粗对比（无需追求提升）
- 判定是否出现类似 v1 的灾难性退化（PSNR 大幅跌落、tLPIPS 爆炸）或吞吐 >2× 且不可控

记录到 `notes/v2_m1_results_owner_a.md`：
- 两个 run 的指标摘要
- 是否满足 “非灾难 + 吞吐可控” 的 Gate M1 结论（PASS/FAIL）
- 若 FAIL：把最短可复现命令与错误现象写清楚，交给 B 修

**Step 6: 刷新 report-pack（文本快照即可）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py
```
Expected: `outputs/report_pack/metrics.csv` 与 `outputs/report_pack/scoreboard.md` 更新，且包含新条目（若脚本按固定前缀扫描）。

---

### Task A3: Gate M2（full600，两次上限）与 evidence 固化（A 接管 GPU 执行）

**Files:**
- Create: `notes/v2_m2_results_owner_a.md`
- Modify: `Progress.md`

**Step 1: 仅在 M1=PASS 时启动 full600 v2（GPU0）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
GPU=0 MAX_STEPS=600 RESULT_TAG=feature_loss_v2_600 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```
Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_600/stats/test_step0599.json`
- `.../videos/traj_4d_step599.mp4`

**Step 2: 启动 full600 v2_gated（GPU0；full600 上限中的第 2 次）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
GPU=0 MAX_STEPS=600 RESULT_TAG=feature_loss_v2_gated_600 \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```
Expected: 同上，产物齐全。

**Step 3: 成功线/止损线判定与记录**

对 `protocol_v1` test@599：
- 成功线：满足任一条（`tLPIPS` ↓≥10% 或 `LPIPS` ↓≥0.01 或 `PSNR` +0.2）
- 若以 `tLPIPS` 达标为主：允许 `PSNR` ≤0.2dB 退化、`LPIPS` ≤ +0.01 退化，但必须后续补 Pareto（由 B/后续执行）

记录到 `notes/v2_m2_results_owner_a.md`：
- 两个 full600 的指标
- 与 baseline/control 的差值
- 是否触发 “两次 full600 无趋势 -> stoploss/Plan‑B 评估”

**Step 4: 刷新 report-pack + 打包 evidence（tar.gz 不入库，sha 入库）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py
python3 scripts/pack_evidence.py
```
Expected:
- `artifacts/report_packs/report_pack_*.tar.gz` 生成
- `artifacts/report_packs/SHA256SUMS.txt` 更新（入库）
- `docs/report_pack/<date>-v*/` 文本快照更新（入库）

**Step 5: 更新全局进度**

Edit `Progress.md`，追加：
- v2 M1/M2 的结论（趋势/失败归因）
- 下一步（是否进入 seg2 / 是否触发 Plan‑B）

**Step 6: 提交并推送 main（仅文本/脚本变更；不提交 outputs/artifacts tar.gz）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260225-v2-gpu-exec
git add notes/v2_m1_results_owner_a.md notes/v2_m2_results_owner_a.md Progress.md docs/report_pack artifacts/report_packs/SHA256SUMS.txt
git commit -m "docs: record feature-loss v2 M1/M2 results and refresh evidence snapshots"
git push origin HEAD:main
```
Expected: push 成功；仓库中只包含文本快照与 sha，不包含大文件。

