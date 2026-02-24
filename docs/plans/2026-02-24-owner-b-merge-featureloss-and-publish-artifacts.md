# Owner B Merge FeatureLoss + Publish Artifacts (Follow-up) Implementation Plan
>
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **Goal:** 将 Owner B 已完成的 `feature_loss_v1` 代码（cache 脚本 + trainer 注入 + runner + 实验记录）合入 `main`，并把关键运行产物（stats/video）发布到主阵地 `outputs/`，以便 Owner C 生成 report-pack/evidence、Owner A 补跑 seg2 anti-cherrypick（A30/A33）。
>
> **Architecture:** 以“cherry-pick 现有 4 个提交”为主（不重写逻辑），再做一次最小 smoke（2 steps）验证集成不破坏 baseline；最后从 B worktree 将 full600 的 `stats/*.json` + `videos/*.mp4` 复制到主阵地 `outputs/`（不入库）。
>
> **Tech Stack:** git worktree/cherry-pick、Bash runners、Python、PyTorch、VGGT（`facebook/VGGT-1B`）、FreeTimeGsVanilla trainer。
>
> ---
>
> **Parallel Safety:** 默认占用 `GPU1`（仅 B39 可选 smoke 用），不阻塞 A（GPU0）与 C（CPU/打包）。
>
> **Non-Goal:** 本轮不继续做 feature-loss 的新设计/大 sweep（已按止损）；不改 `docs/protocol.yaml`（v1 冻结不动）。

---

### Task B36: 建集成 worktree（基于主阵地 main）

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260225-merge-featureloss .worktrees/owner-b-20260225-merge-featureloss main
git -C .worktrees/owner-b-20260225-merge-featureloss status --porcelain=v1
```

Expected:
- worktree 干净。

---

### Task B37: 合入 feature-loss 代码（cherry-pick 4 个既有提交）

目标提交（来自 `owner-b-20260224-vggt-feature-loss-v1`）：
- `f8099ba`（cache 脚本 + 契约测试）
- `0a4fafe`（trainer 注入 feature loss，默认关闭）
- `9b577fd`（runner：`scripts/run_train_feature_loss_selfcap.sh`）
- `668672f`（实验记录：`notes/feature_loss_v1_attempt.md`）

**Step 1: 在集成 worktree 确认提交可见**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-merge-featureloss
git show -s --oneline f8099ba
git show -s --oneline 0a4fafe
git show -s --oneline 9b577fd
git show -s --oneline 668672f
```

Expected:
- 4 条都能 show 出摘要。

**Step 2: cherry-pick**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-merge-featureloss
git cherry-pick f8099ba 0a4fafe 9b577fd 668672f
```

Expected:
- 无冲突直接完成；若有冲突：只解决在 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 的冲突，保持 strong/weak 现有逻辑不回退。

**Step 3: 运行脚本级测试（避免把 main 打挂）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-merge-featureloss
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected:
- 全部 PASS（至少保证 `test_vggt_cache_contract.py`、`test_vggt_feature_loss_flags.py`、现有 weak/strong/adapter/evidence 测试不回归）。

**Step 4: 处理与 C 的文档命名冲突（提前对齐）**

约束：
- 保留 B 的 `notes/feature_loss_v1_attempt.md` 为“带指标的权威记录”。
- 若 C 已有同名“缺失状态”笔记，请让 C 改名为 `notes/feature_loss_v1_status.md`（避免合并冲突）。

验收：
- 集成分支下存在 `notes/feature_loss_v1_attempt.md`，内容为 B 的指标记录版本。

---

### Task B38: 轻量 smoke（可选，GPU1，2 steps，验证 runner 在主阵地可跑）

动机：
- 证明 `scripts/run_train_feature_loss_selfcap.sh` 在 “主阵地环境/venv/路径” 下可用，避免 A/C 复现时才爆。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-merge-featureloss
GPU=1 MAX_STEPS=2 \
RESULT_DIR=outputs/smoke/selfcap_bar_8cam60f/feature_loss_v1_smoke2 \
LAMBDA_VGGT_FEAT=0.005 VGGT_FEAT_START_STEP=0 VGGT_FEAT_EVERY=8 \
bash scripts/run_train_feature_loss_selfcap.sh
```

Expected:
- 产物存在：
  - `outputs/smoke/selfcap_bar_8cam60f/feature_loss_v1_smoke2/stats/test_step0001.json`
  - `outputs/smoke/selfcap_bar_8cam60f/feature_loss_v1_smoke2/videos/traj_4d_step1.mp4`

---

### Task B39: 发布 full600 关键产物到主阵地 `outputs/`（不入库，供 C 打包）

动机：
- C 的 report-pack/evidence 只能从主阵地 `/root/projects/4d-recon/outputs/**/stats/*.json` 与 `videos/*.mp4` 采集。
- 不能用 symlink（`pack_evidence.py` 会把 symlink 原样打包，脱离机器后会断）。

**Step 1: 定位源/目标目录**

源（B worktree，已有 full600 runs）：
- `/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600`
- `/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_retry_lam0.005_s200_600`

目标（主阵地）：
- `/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600`
- `/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_retry_lam0.005_s200_600`

**Step 2: 仅复制 `stats/*.json` + `videos/*.mp4`**

Run:
```bash
SRC_ROOT=/root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1/outputs/protocol_v1/selfcap_bar_8cam60f
DST_ROOT=/root/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f

for RUN in feature_loss_v1_600 feature_loss_v1_retry_lam0.005_s200_600; do
  mkdir -p "$DST_ROOT/$RUN/stats" "$DST_ROOT/$RUN/videos"
  cp -f "$SRC_ROOT/$RUN/stats/"*.json "$DST_ROOT/$RUN/stats/"
  cp -f "$SRC_ROOT/$RUN/videos/"*.mp4 "$DST_ROOT/$RUN/videos/"
done
```

Expected:
- 目标目录下至少存在：
  - `.../stats/val_step0599.json`
  - `.../stats/test_step0599.json`
  - `.../videos/traj_4d_step599.mp4`

**Step 3: 让 report-pack 能抓到新行（本地生成，不入库也可）**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
rg -n \"feature_loss_v1\" outputs/report_pack/metrics.csv | head
```

Expected:
- 能 grep 到 `feature_loss_v1_600` 与 `feature_loss_v1_retry_lam0.005_s200_600` 的指标行（stage=test/val）。

**Step 4: 通知 C/A**

输出给团队（粘贴到群里即可）：
- `scripts/run_train_feature_loss_selfcap.sh` 已在集成分支可用（合入 main 后 A 可跑 seg2）。
- 主阵地已出现两个 run 的关键产物目录（上面的 `DST_ROOT/...`）。
- C 可以立刻重刷 report-pack + 重新打 evidence v8（或 v9）。

---

### Task B40: 合入 `main`（由你或集成负责人执行）

Run（在集成 worktree）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-merge-featureloss
git log --oneline --decorate --max-count=10
```

交付二选一：
1. 你直接 push（团队确认后执行）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-merge-featureloss
git push origin HEAD:main
```
2. 你不 push，仅把集成分支 HEAD 提交号发给集成负责人，让他在主阵地做 merge。

验收：
- `main` 具备：
  - `scripts/precompute_vggt_cache.py`
  - `scripts/run_train_feature_loss_selfcap.sh`
  - trainer flags 与 loss hook（`lambda_vggt_feat` 等）
  - `notes/feature_loss_v1_attempt.md`

