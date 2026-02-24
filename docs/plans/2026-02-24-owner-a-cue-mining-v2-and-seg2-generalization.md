# Owner A Cue Mining V2 + Seg2 Generalization Plan (Next)

> 状态：待执行（Next）。本计划面向 `2026-02-26` 起的后续推进（多场景/可解释 cue mining），不影响当前 `docs/protocol.yaml`（v1）midterm 口径。

我在使用 **writing-plans** skill 来写这份计划。未使用 brainstorming skill 的原因：本阶段目标与约束已在 `docs/execution/2026-02-12-4d-reconstruction-execution.md#6-2026-02-26-起后续推进路线` 与 `docs/protocol.yaml` 中明确，直接落到可执行任务更省时间。

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 cue mining 从 “diff fallback 可跑” 升级到 “可解释/可诊断/可复现”，并完成一次 anti-cherrypick 的 **second segment**（同 SelfCap bar，不同帧段）baseline vs ours-weak 对比，为 3 月多场景扩展打底。

**Parallel Safety:** Owner A 主要占用 `GPU0`（必要时），不阻塞 Owner B（strong 机制改进）与 Owner C（报告/证据包/多场景表格）。

**Non-Goal (本轮不做):**
- 不改动 `docs/protocols/protocol_v1.yaml`（midterm 口径保持冻结）。
- 不在本轮强行把 cue mining 绑定到某个外部大模型（VGGT 若继续阻塞，必须有可解释 fallback）。
- 不追求 strong 指标领先（strong 的后续由 B 主导）。

---

## Task A23: 创建隔离 Worktree/分支

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260224-cuev2-seg2 .worktrees/owner-a-20260224-cuev2-seg2 main
git -C .worktrees/owner-a-20260224-cuev2-seg2 status --porcelain=v1
```

Expected:
- worktree 干净。

---

## Task A24: Cue Mining “质量诊断”产物（让 stoploss 可机器判定）

动机：
- 当前 cue mining（`scripts/cue_mining.py`）输出 `pseudo_masks.npz` + 2 张 viz，但缺少“质量指标/失败信号”的结构化输出，导致后续多场景扩展时排查成本高。

**Files:**
- Modify: `scripts/cue_mining.py`
- Modify: `scripts/run_cue_mining.sh`
- Create: `scripts/tests/test_cue_mining_quality_stats.py`
- Update: `notes/cue_mining_spec.md`

**Step 1: 在 cue mining 输出目录新增 `quality.json`（MVP keys）**
- 写入：
  - `mask_mean_per_t`（长度 T 的列表，0..1）
  - `mask_mean_per_view`（长度 V）
  - `mask_min` / `mask_max`
  - `temporal_flicker_l1_mean`（基于 `|mask[t]-mask[t-1]|` 的均值）
  - `all_black` / `all_white`（硬止损信号）

**Step 2: `run_cue_mining.sh` 打印质量摘要**
- 输出一行 summary（便于 log grep）：mask mean/min/max、flicker、black/white flags。

**Step 3: 单测（不依赖 pytest）**
- 用现有 `scripts/tests/test_cue_mining_contract.py` 的 synthetic 数据路径复用/或新建极小 synthetic；
- 断言 `quality.json` 存在且 keys 完整，`all_black/all_white` 为 bool。

验收：
- 对 `outputs/cue_mining/selfcap_bar_8cam60f_v1/` 复跑后产生 `quality.json`，且不影响现有 `pseudo_masks.npz` 契约。

---

## Task A25 (Timebox 1d): VGGT backend 再尝试，但必须“可审计止损”

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

## Task A26: Second Segment 数据集（anti-cherrypick）生成

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

## Task A27: Seg2 上 baseline vs ours-weak（同预算 600-step）

原则（避免 cherry-pick）：
- Seg2 **不允许**为了“让 seg2 更好看”而重调超参；必须复用主段（v1）最终拍板的弱融合参数（例如 `PSEUDO_MASK_WEIGHT/PSEUDO_MASK_END_STEP`）。

**Runs (GPU0):**
- baseline：
  - `DATA_DIR=data/selfcap_bar_8cam60f_seg200_260`
  - `RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600`
- ours-weak（沿用 tuned defaults）：
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

## Task A28: 写入 “anti-cherrypick” 记录与结论（供 C 打包）

**Files:**
- Create: `notes/anti_cherrypick_seg200_260.md`

内容要求：
- 写明 seg2 的生成命令、数据路径、对应的 2 个 run_dir；
- 粘贴 test@step599 指标（PSNR/SSIM/LPIPS/tLPIPS）；
- 结论：是否在 second segment 仍保持 “not worse than baseline”，以及失败模式是否变化。

验收：
- C 可直接把该文档与 seg2 的 metrics 行纳入后续 evidence pack。
