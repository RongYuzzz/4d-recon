# Owner A Merge Defenses + Seg2 FeatureLoss (Follow-up) Implementation Plan
>
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **Goal:** 把 A 已完成的 defense 类交付（cue overlay + velocity stats）稳定合入 `main`，并在 feature-loss 主线可用后补齐 seg2 的 feature-loss anti-cherrypick 证据（可选但推荐）。
>
> **Architecture:** 分两条线并行推进：先把纯诊断/文档改动以小提交合入主线，保证 C 的 report-pack/evidence 能引用；feature-loss 的 seg2 补跑单独在隔离分支跑 GPU0，产物仅落 `outputs/` 与 `notes/`，不改 `docs/protocol.yaml`。
>
> **Tech Stack:** git worktree/branch、Python（`scripts/cue_mining.py`、`scripts/export_velocity_stats.py`）、Bash runners、FreeTimeGsVanilla trainer。
>
> ---
>
> **Parallel Safety:** 默认占用 `GPU0`（仅 A33 跑训练需要 GPU），不阻塞 B（feature-loss 合并/产物落地）与 C（scoreboard/evidence 刷新）。
>
> **Non-Goal:** 不改 `docs/protocol.yaml`（v1 冻结不动）；不做新的算法改动（只做证据与复现闭环）。

---

### Task A31: 将 A24b/A29 交付形成可审计 commit（合入主线前置）

**Files:**
- Modify: `scripts/cue_mining.py`
- Modify: `scripts/tests/test_cue_mining_contract.py`
- Modify: `notes/cue_mining_spec.md`
- Create: `scripts/export_velocity_stats.py`
- Create: `scripts/tests/test_export_velocity_stats.py`
- Create: `notes/velocity_stats_selfcap_bar_8cam60f.md`
- Modify: `notes/anti_cherrypick_seg200_260.md`

**Step 1: 在 A worktree 确认当前状态与差异**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
git status --porcelain=v1
git diff --stat
```

Expected:
- 存在上述文件的 `M/??` 变更（与汇报一致）。

**Step 2: 跑 A 相关最小单测集**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
python3 scripts/tests/test_cue_mining_contract.py
python3 scripts/tests/test_cue_mining_quality_stats.py
python3 scripts/tests/test_export_velocity_stats.py
```

Expected:
- 全部 PASS。

**Step 3: 以“功能拆分”方式提交（建议 2 个 commit）**

Commit 1（overlay 扩充）：
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
git add scripts/cue_mining.py scripts/tests/test_cue_mining_contract.py notes/cue_mining_spec.md
git commit -m "feat(cue-mining): add per-cam overlay outputs for sanity check"
```

Commit 2（velocity stats + 记录收口）：
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
git add scripts/export_velocity_stats.py scripts/tests/test_export_velocity_stats.py notes/velocity_stats_selfcap_bar_8cam60f.md notes/anti_cherrypick_seg200_260.md
git commit -m "feat(diagnostics): export velocity stats md for defense pack"
```

Expected:
- `git status --porcelain=v1` 为空。

**Step 4: 将 commit 提交号同步给集成负责人**

输出：
- 两个 commit hash（用于 cherry-pick/merge）。

验收：
- commit 可被干净 cherry-pick 到 `/root/projects/4d-recon` 的 `main`。

---

### Task A32: 合入主线后的可引用性检查（不跑训练）

动机：
- 确保 C 的 evidence/report-pack 能稳定引用新脚本与文档（不依赖 A 的 worktree 路径）。

**Step 1: 在主阵地检查文件存在**

Run:
```bash
cd /root/projects/4d-recon
ls -la scripts/export_velocity_stats.py
ls -la notes/velocity_stats_selfcap_bar_8cam60f.md
```

Expected:
- 文件存在（由集成负责人合并后满足）。

**Step 2: 在主阵地跑最小单测**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_export_velocity_stats.py
python3 scripts/tests/test_cue_mining_contract.py
```

Expected:
- PASS。

---

### Task A33（可选但推荐，GPU0，约 1 次 full600）: Seg2 补跑 feature_loss_v1（anti-cherrypick）

前置条件（满足其一即可执行）：
- `main` 已包含 B 的 feature-loss 代码与 runner（至少 `scripts/run_train_feature_loss_selfcap.sh` 存在）。
- 或者在隔离分支上临时 cherry-pick B 的 3 个 code 提交：`f8099ba`、`0a4fafe`、`9b577fd`（仅用于跑出 seg2 产物，后续以 main 为准）。

**Step 1: 确认 seg2 数据存在**

Run:
```bash
cd /root/projects/4d-recon
ls -la data/selfcap_bar_8cam60f_seg200_260/triangulation | head
```

Expected:
- 存在 `points3d_frame000000.npy` 等文件。

**Step 2: 运行 feature_loss（使用 B 的“止损后最好配置”，不在 seg2 上调参）**

Run（GPU0）：
```bash
cd /root/projects/4d-recon
GPU=0 MAX_STEPS=600 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/feature_loss_v1_600 \
LAMBDA_VGGT_FEAT=0.005 VGGT_FEAT_START_STEP=200 VGGT_FEAT_EVERY=8 \
bash scripts/run_train_feature_loss_selfcap.sh
```

Expected:
- 目录生成：
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/feature_loss_v1_600/stats/test_step0599.json`
  - `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/feature_loss_v1_600/videos/traj_4d_step599.mp4`

**Step 3: 更新 seg2 记录（anti-cherrypick 文档追加一节即可）**

Files:
- Modify: `notes/anti_cherrypick_seg200_260.md`

内容要求：
- 追加 feature_loss_v1 的 test@step599 指标（PSNR/SSIM/LPIPS/tLPIPS）。
- 结论一句话：feature_loss_v1 在 seg2 上是否同样“无收益/退化/接近 baseline”。

**Step 4: 通知 C 刷新 report-pack/evidence**

输出给 C：
- `RESULT_DIR` 路径（feature_loss_v1_600 seg2）。
- 更新后的 `notes/anti_cherrypick_seg200_260.md` 已包含新指标。

验收：
- C 可在主阵地执行：
  - `python3 scripts/build_report_pack.py ...`
  - `python3 scripts/summarize_scoreboard.py ...`
  - `python3 scripts/pack_evidence.py ...`
  并把 seg2 feature-loss 行纳入最新 evidence 快照。

