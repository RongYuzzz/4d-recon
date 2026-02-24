# Owner A Cue Mining V2 + Seg2 Generalization Plan (Next)

> 状态：部分已完成（截至 `2026-02-24`：`A23-A28` 已完成；剩余 `A24b`（overlay 扩充）/ `A29`（速度统计页）/ `A30`（seg2 feature_loss，对 B 合并有弱依赖））。本计划面向 `2026-02-26` 起的后续推进（多场景/可解释 cue mining），不影响当前 `docs/protocol.yaml`（v1）midterm 口径。

我在使用 **writing-plans** skill 来写这份计划。未使用 brainstorming skill 的原因：本阶段目标与约束已在 `docs/execution/2026-02-12-4d-reconstruction-execution.md#6-2026-02-26-起后续推进路线` 与 `docs/protocol.yaml` 中明确，直接落到可执行任务更省时间。

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 cue mining 从 “diff fallback 可跑” 升级到 “可解释/可诊断/可复现”，并完成一次 anti-cherrypick 的 **second segment**（同 SelfCap bar，不同帧段）对比（baseline vs 当前主线方法），为 3 月多场景扩展打底。

**Parallel Safety:** Owner A 主要占用 `GPU0`（必要时），不阻塞 Owner B（VGGT feature metric loss 主线）与 Owner C（scoreboard/evidence/报告）。

**Non-Goal (本轮不做):**
- 不改动 `docs/protocols/protocol_v1.yaml`（midterm 口径保持冻结）。
- 不在本轮强行把 cue mining 绑定到某个外部大模型（VGGT 若继续阻塞，必须有可解释 fallback）。
- 不把 KLT strong v2 当主线（KLT 仅作为 attempt/bridge 的可审计 baseline；主线是 VGGT feature-level prior）。

---

## 现状（Reality Check，便于并行推进）

- 已存在隔离 worktree：`.worktrees/owner-a-20260224-cuev2-seg2`
- cue mining 已具备结构化质量产物：`quality.json` + `scripts/tests/test_cue_mining_quality_stats.py`
- `--backend vggt` 已可运行且有审计记录：`notes/vggt_setup.md`
- seg2 anti-cherrypick 已完成（baseline vs ours-weak，600 steps）：`notes/anti_cherrypick_seg200_260.md`
- seg2 协议已冻结（仅改帧段/数据 root）：`docs/protocols/protocol_v1_seg200_260.yaml`

本计划的新增交付主要集中在：
- cue overlay 扩充（更快定位坐标系/值域问题）
- `||v||` 速度统计页（答辩防守证据）
- （可选）seg2 上补跑 feature_loss（对齐 B 的主线）

---

## Task A23: 创建隔离 Worktree/分支（DONE）

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260224-cuev2-seg2 .worktrees/owner-a-20260224-cuev2-seg2 main
git -C .worktrees/owner-a-20260224-cuev2-seg2 status --porcelain=v1
```

Expected:
- worktree 干净。

---

## Task A24: Cue Mining “质量诊断”产物（DONE，尚需补 overlay 扩充）

动机：
- 当前 cue mining（`scripts/cue_mining.py`）输出 `pseudo_masks.npz` + 2 张 viz，但缺少“质量指标/失败信号”的结构化输出，导致后续多场景扩展时排查成本高。

**Files:**
- Modify: `scripts/cue_mining.py`
- Modify: `scripts/run_cue_mining.sh`
- Create: `scripts/tests/test_cue_mining_quality_stats.py`
- Update: `notes/cue_mining_spec.md`

**Step 1: `quality.json`（DONE）**
- 现已写入：
  - `mask_mean_per_t`（长度 T 的列表，0..1）
  - `mask_mean_per_view`（长度 V）
  - `mask_min` / `mask_max`
  - `temporal_flicker_l1_mean`（基于 `|mask[t]-mask[t-1]|` 的均值）
  - `all_black` / `all_white`（硬止损信号）

**Step 2: `run_cue_mining.sh` 打印质量摘要（DONE）**
- 输出一行 summary（便于 log grep）：mask mean/min/max、flicker、black/white flags。

**Step 3: Cue 对齐 sanity overlay 扩充（TODO，不影响现有契约）**
- 当前已产出：
  - `viz/overlay_cam02_frame000000.jpg`
  - `viz/grid_frame000000.jpg`
- 需要补齐（不破坏已有输出文件名）：
  - 对每个 cam 额外输出少量固定命名的 overlay（例如每 cam 抽 2 帧）：
    - `overlay_cam<cam>_frame000000.jpg`
    - `overlay_cam<cam>_frame000030.jpg`
- 目的：快速确认 cam/frame 索引、resize/坐标系、值域方向（dynamic=1 还是 static=1）没有反。

**Step 4: 单测（DONE，不依赖 pytest）**
- 用现有 `scripts/tests/test_cue_mining_contract.py` 的 synthetic 数据路径复用/或新建极小 synthetic；
- 断言 `quality.json` 存在且 keys 完整，`all_black/all_white` 为 bool。

验收：
- 对 `outputs/cue_mining/selfcap_bar_8cam60f_v1/` 复跑后产生 `quality.json`，且不影响现有 `pseudo_masks.npz` 契约。

---

## Task A25 (Timebox 1d): VGGT backend 再尝试，但必须“可审计止损”（DONE）

动机：
- 论文叙事希望从 “纯帧差分” 走向 “training-free 语义 cue/attention”，VGGT 是优先路线。

**Files:**
- Update: `notes/vggt_setup.md`
- (Optional) Add: `third_party/VGGT/`（或仅记录外部路径与版本信息，不强制入库大权重）
- Modify: `scripts/cue_mining.py`（让 `--backend vggt` 真正可用，或明确止损）

交付二选一（必须完成其一）：
1. **成功版**：`--backend vggt` 可在 `data/selfcap_bar_8cam60f` 60 帧上产出 `pseudo_masks.npz + quality.json + viz/`，并在 `notes/vggt_setup.md` 写清：
   - 安装/权重来源
   - 版本 hash/commit
   - 运行命令与耗时
2. **止损版**：如果依赖/权重/环境不可控，更新 `notes/vggt_setup.md` 写清：
   - 具体阻塞点
   - 是否可通过离线权重/容器解决
   - 后续替代路线（例如：基于特征的轻量 clustering backend）

验收：
- 任何情况下 `--backend vggt` 的失败必须是“立即失败 + 给出下一步指引”，不得 silent fallback（避免污染实验）。

---

## Task A26: Second Segment 数据集（anti-cherrypick）生成（DONE）

选择：
- 同一 SelfCap bar（`bar-release.tar.gz`），不同帧段，例如 `frame_start=200 num_frames=60`。

**Files:**
- (data only) Create: `data/selfcap_bar_8cam60f_seg200_260/`（不入库）
- Create: `docs/protocols/protocol_v1_seg200_260.yaml`（仅作为 anti-cherrypick 附录协议：**与 v1 完全同参**，只改变数据 root/帧段；不替换 `docs/protocol.yaml`）

Run（示例）：
```bash
cd /root/projects/4d-recon
PY=third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz data/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg200_260 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 200 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

验收：
- `data/selfcap_bar_8cam60f_seg200_260/images/*/000000.jpg` 存在；
- `triangulation/points3d_frame*.npy` 为 60；
- `sparse/0/*.bin` 存在。

---

## Task A27: Seg2 上对比实验（同预算 600-step）（DONE：baseline vs ours-weak）

原则（避免 cherry-pick）：
- Seg2 **不允许**为了“让 seg2 更好看”而重调超参；必须复用主段（v1）最终拍板的弱融合参数（例如 `PSEUDO_MASK_WEIGHT/PSEUDO_MASK_END_STEP`）。

**Runs (GPU0):**
- baseline：
  - `DATA_DIR=data/selfcap_bar_8cam60f_seg200_260`
  - `RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600`
- 主线方法（二选一，优先 vggt feature loss；若尚未集成则先跑 weak 作为占位）：
  1. `feature_loss_v1`（由 Owner B 集成后启用）：
     - `RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/feature_loss_v1_600`
  2. `ours-weak`（fallback，占位对比）：
     - `CUE_TAG=selfcap_bar_8cam60f_seg200_260_v1`（避免覆盖主段）
     - `PSEUDO_MASK_WEIGHT=0.3`、`PSEUDO_MASK_END_STEP=200`
     - `RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/ours_weak_600`

Run（示例）：
```bash
cd /root/projects/4d-recon

GPU=0 MAX_STEPS=600 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600 \
bash scripts/run_train_baseline_selfcap.sh

# Option A (preferred): feature loss v1 (when available)
# GPU=0 MAX_STEPS=600 \
# DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
# RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/feature_loss_v1_600 \
# bash scripts/run_train_feature_loss_selfcap.sh

# Option B (fallback): ours-weak (placeholder)
GPU=0 MAX_STEPS=600 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/ours_weak_600 \
CUE_TAG=selfcap_bar_8cam60f_seg200_260_v1 \
PSEUDO_MASK_WEIGHT=0.3 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh

python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

验收：
- 两个目录都有 `videos/traj_4d_step599.mp4` + `stats/{val,test}_step0599.json`
- `outputs/report_pack/metrics.csv` 出现 seg2 两行（val/test）

---

## Task A28: 写入 “anti-cherrypick” 记录与结论（供 C 打包）（DONE）

**Files:**
- Create: `notes/anti_cherrypick_seg200_260.md`

内容要求：
- 写明 seg2 的生成命令、数据路径、对应的 2 个 run_dir；
- 粘贴 test@step599 指标（PSNR/SSIM/LPIPS/tLPIPS）；
- 结论：是否在 second segment 仍保持 “not worse than baseline”，以及失败模式是否变化。

验收：
- C 可直接把该文档与 seg2 的 metrics 行纳入后续 evidence pack。

---

## Task A29: 速度统计页（答辩防守证据：反驳 “zero velocity 死路” 类攻击）

动机：
- 外部评审要求补齐两页“可展示证据”：`||v||` 分布统计 + cue 对齐 sanity。
- cue 对齐已在 A24 输出更多 overlay；这里补齐 `||v||` 分布统计页，避免口头争论。

**Files:**
- Create: `scripts/export_velocity_stats.py`
- Create: `scripts/tests/test_export_velocity_stats.py`
- Create: `notes/velocity_stats_selfcap_bar_8cam60f.md`

**Step 1: 从 init NPZ 导出 step0 速度统计**
- 输入：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz`
- 输出（写入 md）：
  - `||v||` 的 min/mean/p50/p90/p99/max
  - `ratio(||v|| < eps)`（eps 固定，比如 `1e-4`）
  - `times/durations` 的 min/mean/max（证明时间归一化与 duration 初始化口径）

**Step 2: 从 ckpt 导出 step599（end）速度统计**
- 输入：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/ckpts/ckpt_599.pt`
- 输出（写入 md）：
  - 与 step0 同一套统计口径（便于对比）

**Step 3（可选）: 导出 step100 统计（如果评审强要求 0/100/600 三点）**
- 方式 A（推荐，最省改动）：跑一个 “诊断短跑” baseline：
  - `MAX_STEPS=101`，并让 save/eval 对齐到最后一步（保证出 ckpt 与 stats）
  - 结果目录：`outputs/diagnostics/selfcap_bar_8cam60f/baseline_101`
- 方式 B：在训练时开 `T0_DEBUG_INTERVAL=100`，从日志抓取 step100 的 `||v||` 统计并固化到 md。

**Step 4: 单测**
- 用极小的 synthetic NPZ/CKPT fixture（或 mock）验证：
  - 脚本 CLI 能跑通
  - 输出 md 至少包含必需字段（min/mean/p50/p90/p99/max、ratio<eps）

验收：
- `notes/velocity_stats_selfcap_bar_8cam60f.md` 可直接被 C 纳入 evidence pack；
- 该页至少包含 step0 与 step599 的对比（step100 作为可选增强）。

---

## Task A30（可选，弱依赖 B）：Seg2 上补跑 feature_loss_v1（对齐主线）

动机：
- seg2 目前只做了 baseline vs ours-weak。若 B 的 feature_loss_v1 成为主线，需要在 seg2 上补一条 “anti-cherrypick: baseline vs feature_loss_v1” 的证据，避免只在主段成立。

前置：
- `scripts/run_train_feature_loss_selfcap.sh` 已合入 `main`（由 Owner B 交付）。

Runs（GPU0）：
- `DATA_DIR=data/selfcap_bar_8cam60f_seg200_260`
- `RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/feature_loss_v1_600`

验收：
- `notes/anti_cherrypick_seg200_260.md` 追加一段 feature_loss_v1 的 test@step599 指标与结论（不需要重写全文）。
