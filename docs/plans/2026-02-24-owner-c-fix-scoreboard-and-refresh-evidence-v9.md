# Owner C Fix Scoreboard + Refresh Evidence v9 (Follow-up) Implementation Plan
>
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **Goal:** 修复 `scripts/summarize_scoreboard.py` 的“风险提示”逻辑与 feature-loss 变体纳入问题，并在 A/B 产物落地主阵地后，生成可审计的 report-pack/evidence **v9**（避免覆盖 v8）。
>
> **Architecture:** 先做纯代码修复（scoreboard 逻辑 + 单测），不依赖 GPU；再等待 B 发布 `feature_loss_v1*` 的 `stats/videos` 到主阵地 `outputs/` 后重刷 `outputs/report_pack/*`，最后用 `scripts/pack_evidence.py` 打包并写入 `docs/report_pack/<DATE>-v9/` 快照与 `artifacts/report_packs/SHA256SUMS.txt`。
>
> **Tech Stack:** Python（csv/json）、Bash、现有脚本（`scripts/build_report_pack.py`、`scripts/summarize_scoreboard.py`、`scripts/pack_evidence.py`）、脚本级测试（`scripts/tests/test_*.py`）。
>
> ---
>
> **Parallel Safety:** 全程 CPU/IO 为主，不占用 GPU；仅在最终打包时需要读 `outputs/**/videos/*.mp4`。
>
> **Non-Goal:** 不改 `docs/protocol.yaml`（v1 冻结不动）；不做新的算法实验；不在本计划里“重跑训练”。

---

### Task C30: 建隔离 worktree（避免污染 main）

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-c-20260225-evidence-v9 .worktrees/owner-c-20260225-evidence-v9 main
git -C .worktrees/owner-c-20260225-evidence-v9 status --porcelain=v1
```

Expected:
- worktree 干净。

---

### Task C31: 修复 scoreboard 对 feature-loss 变体的收录（TDD）

动机：
- 当前 `main` 的 `scripts/summarize_scoreboard.py` 没有纳入 `feature_loss_v1*` 变体，导致 B 的结果即使落地也不会出现在 scoreboard。

**Files:**
- Modify: `scripts/summarize_scoreboard.py`
- Modify: `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 让测试用例覆盖 feature-loss 变体**

动作：
- 在 `scripts/tests/test_summarize_scoreboard.py` 的最小 `metrics.csv` fixture 中增加两行：
  - `feature_loss_v1_600`
  - `feature_loss_v1_retry_lam0.005_s200_600`（可选，但建议也收录，便于对照止损调参）

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- FAIL（未包含 feature-loss 行，或筛选逻辑漏掉）。

**Step 2: 最小实现：纳入 feature-loss 变体**

实现要求：
- `scripts/summarize_scoreboard.py` 识别 `feature_loss_v1*_600` 与 `feature_loss_v1_retry*_600`（只要以 `feature_loss_v1` 开头并包含 `_600` 即可）。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- PASS。

**Step 3: commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py
git commit -m "fix(scoreboard): include feature-loss variants in selection"
```

---

### Task C32: 修复 “风险提示” 判断方向（TDD）

动机：
- 指标方向：`tLPIPS/LPIPS` 越低越好，`PSNR/SSIM` 越高越好。
- 风险提示应在 **control 优于 ours_weak** 时标红；当前逻辑容易写反。

**Files:**
- Modify: `scripts/summarize_scoreboard.py`
- Modify: `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 写一个会触发风险提示的 fixture（control 明显更好）**

动作：
- 在测试 fixture 里设置：
  - `ours_weak_600`: `lpips=0.41`, `tlpips=0.03`
  - `control_weak_nocue_600`: `lpips=0.39`, `tlpips=0.02`
- 断言：输出 markdown 必须包含风险提示行。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- FAIL（方向写反时会不提示或提示错误）。

**Step 2: 实现正确方向**

规则（优先级从高到低）：
- 若 `control.tLPIPS < ours_weak.tLPIPS`：标红
- else 若 `control.LPIPS < ours_weak.LPIPS`：标红
- else 若 `control.PSNR > ours_weak.PSNR`：标红
- else 若 `control.SSIM > ours_weak.SSIM`：标红
- 否则不提示

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected:
- PASS。

**Step 3: commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py
git commit -m "fix(scoreboard): correct risk-hint direction (control better than ours_weak)"
```

---

### Task C33: 解决 feature-loss 相关 notes 的命名冲突（与 B 对齐）

动机：
- B 已交付“带指标的权威记录” `notes/feature_loss_v1_attempt.md`。
- C 之前若有同名“缺失状态”笔记，会与 B 冲突，必须改名。

**Files:**
- Create: `notes/feature_loss_v1_status.md`（如果需要状态说明）
- (Optional) Delete: `notes/feature_loss_v1_attempt.md`（仅当该文件是 C 的占位缺失说明，且未包含实验指标）

**Step 1: 检查当前主线 notes 是否已有同名文件**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
ls -la notes | rg -n "feature_loss_v1_"
```

Expected:
- 若存在 `notes/feature_loss_v1_attempt.md` 且内容是“缺失状态”，则改名为 `notes/feature_loss_v1_status.md`。

**Step 2: commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
git add notes/feature_loss_v1_status.md
git rm -f notes/feature_loss_v1_attempt.md || true
git commit -m "docs(notes): avoid feature-loss attempt note name conflict (use status note)"
```

---

### Task C34: 等待 B 发布产物到主阵地 outputs（阻塞点，C 不主动生成）

依赖（由 B 完成，见其计划 B39）：
- `/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600/stats/test_step0599.json`
- `/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600/videos/traj_4d_step599.mp4`
- （可选）retry 目录同样落地

检查：
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
ls -la /root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600/stats/test_step0599.json
ls -la /root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600/videos/traj_4d_step599.mp4
```

Expected:
- 两个文件存在后，进入 C35。

---

### Task C35: 重刷 report-pack + scoreboard（把 feature-loss 行写进 metrics）

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
rg -n "feature_loss_v1" /root/projects/4d-recon/outputs/report_pack/metrics.csv | head
```

Expected:
- `metrics.csv` 中出现 feature-loss 行。

---

### Task C36: 生成 evidence v9（主阵地 artifacts + docs 快照 + SHA256）

**Step 1: 打包**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
DATE="$(date +%F)"
python3 scripts/pack_evidence.py --repo_root /root/projects/4d-recon --out_tar "/root/projects/4d-recon/artifacts/report_packs/report_pack_${DATE}-v9.tar.gz"
sha256sum "/root/projects/4d-recon/artifacts/report_packs/report_pack_${DATE}-v9.tar.gz"
```

Expected:
- 打印 sha256，tarball 生成成功。

**Step 2: 解出文本快照到 docs/report_pack/<DATE>-v9/**

说明：
- 快照只存文本（`metrics.csv/scoreboard.md/notes`），不把 mp4 放进 git。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
DATE="$(date +%F)"
OUT_DIR="/root/projects/4d-recon/docs/report_pack/${DATE}-v9"
mkdir -p "$OUT_DIR"
cp -f /root/projects/4d-recon/outputs/report_pack/metrics.csv "$OUT_DIR/metrics.csv"
cp -f /root/projects/4d-recon/outputs/report_pack/scoreboard.md "$OUT_DIR/scoreboard.md"
cp -f /root/projects/4d-recon/outputs/report_pack/ablation_notes.md "$OUT_DIR/ablation_notes.md"
cp -f /root/projects/4d-recon/outputs/report_pack/failure_cases.md "$OUT_DIR/failure_cases.md"
cp -f /root/projects/4d-recon/outputs/report_pack/manifest_sha256.csv "$OUT_DIR/manifest_sha256.csv"
```

**Step 3: 更新 SHA256SUMS.txt（入库）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
DATE="$(date +%F)"
SHA="$(sha256sum /root/projects/4d-recon/artifacts/report_packs/report_pack_${DATE}-v9.tar.gz | awk '{print $1}')"
grep -q "report_pack_${DATE}-v9.tar.gz" /root/projects/4d-recon/artifacts/report_packs/SHA256SUMS.txt || \
  echo "${SHA}  artifacts/report_packs/report_pack_${DATE}-v9.tar.gz" >> /root/projects/4d-recon/artifacts/report_packs/SHA256SUMS.txt
```

**Step 4: 运行关键单测**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_pack_evidence.py
```

Expected:
- PASS。

**Step 5: commit（只入库 docs 快照 + SHA256SUMS + scoreboard 修复）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
DATE="$(date +%F)"
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py
git add /root/projects/4d-recon/artifacts/report_packs/SHA256SUMS.txt
git add "/root/projects/4d-recon/docs/report_pack/${DATE}-v9"
git add notes/feature_loss_v1_status.md || true
git commit -m "docs(report-pack): snapshot v9 (feature-loss included) and fix scoreboard risk hints"
```

验收：
- `docs/report_pack/<DATE>-v9/scoreboard.md` 中出现 feature-loss 行与正确的风险提示（若触发）。
- `artifacts/report_packs/report_pack_<DATE>-v9.tar.gz` 存在，且 SHA256SUMS 已登记。

---

### Task C37: 主线同步（push 前置检查）

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-c-20260225-evidence-v9
git fetch origin
git log --oneline --decorate --left-right origin/main...HEAD | head -n 30
git status --porcelain=v1
```

交付：
- 若确认无分叉且允许 push：
  - `git push origin HEAD:main`
- 否则：把 `HEAD` 提交号发给集成负责人，由其做 merge/push。

