# Owner A VGGT Cue Mining + Weak Fusion Plan (Next)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不破坏现有 baseline/Gate-0/Gate-1 可复现性的前提下，补齐“创新主线”的最小可交付：`cue mining(训练前/不finetune)` 产出 `pseudo_mask`，并以**弱融合**形式接入训练（mask-weighted photometric loss 或等价的低风险入口），形成 `Baseline vs Ours-Weak` 的可复现实验脚本与证据。

**Non-Goal (本轮不做):**
- 不做 strong fusion（attention-guided correspondence/contrastive loss），只预留 I/O 契约与扩展点。
- 不追求多场景刷榜；优先单场景在 `SelfCap bar 8cam60f` 上闭环可复现。

**Parallel Safety:** 本计划新增功能默认全关闭；不要求 B/C 等待即可继续跑 baseline、打包证据、准备汇报材料。

**Default Resources:** A 使用 `GPU0` 做最小 smoke（`max_steps=60~200`），其余流程 CPU 即可。

---

## Task A11: 创建隔离 Worktree/分支（避免污染 main）

**Files:**
- None (worktree only)

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260224-vggt-weak .worktrees/owner-a-20260224-vggt-weak main
git -C .worktrees/owner-a-20260224-vggt-weak status --porcelain=v1
```

Expected:
- worktree 干净（`status` 输出为空）

---

## Task A12: 冻结 Cue Mining 输入输出契约（先写 spec 再写代码）

**Files:**
- Create: `notes/cue_mining_spec.md`

Spec 最小要求（MVP）：
- 输入：`data/<dataset>/images/<cam_name>/<frame>.jpg`（复用现有 SelfCap 目录）
- 输出目录：`outputs/cue_mining/<tag>/`
- 输出文件（MVP）：
  - `pseudo_masks.npz`（必须包含 keys）：
    `masks` (`uint8`, shape=`[T, V, Hm, Wm]`, 值域 `{0,1}` 或 `[0,255]`)
    `camera_names` (`str[V]`, 按文件夹排序)
    `frame_start` (`int`)
    `num_frames` (`int`, 等于 T)
    `mask_downscale` (`int`, 例如 `4`)
  - `viz/`：至少导出 1 张 overlay 拼图（便于汇报截图），命名固定可复用

验收：
- spec 写清楚“如何从训练 sample 的 `frame_offset/camera_idx` 映射到 mask index”

---

## Task A13: 实现 Cue Mining MVP（先做可运行基线，VGGT 后端可插拔）

**Files:**
- Create: `scripts/run_cue_mining.sh`
- Create: `scripts/cue_mining.py`（或 `scripts/cue_mining/*.py`，按你习惯）
- Create: `scripts/tests/test_cue_mining_contract.py`

**Step 1: MVP 后端（不依赖外部权重）**
- 用 “frame difference / temporal high-frequency” 生成粗 mask（每 view 独立）：
  - `gray(t) - gray(t-1)` 做 abs diff
  - 自适应阈值（分位数/均值+std）+ 形态学去噪（可选）
  - 统一降采样到 `mask_downscale=4`（避免 NPZ 体积爆炸）

**Step 2: VGGT 后端接口（可选实现，不阻塞 MVP）**
- 在 `scripts/cue_mining.py` 中加 `--backend {diff,vggt}`：
  - `diff` 永远可用（作为兜底）
  - `vggt`：若未安装/未找到权重，给出明确报错与下一步指引（写到 `notes/vggt_setup.md` 可选）

**Step 3: 可视化**
- 输出 `outputs/cue_mining/<tag>/viz/`：
  - `overlay_cam02_frame000000.jpg`（固定命名便于引用）
  - `grid_frame000000.jpg`（多视角拼图，1 张即可）

**Step 4: 单测（不依赖 pytest）**
- `test_cue_mining_contract.py`：用 `scripts/generate_synthetic_scene01.py` 生成极小数据（比如 2 cams × 3 frames），跑 cue mining 并断言 `pseudo_masks.npz` 存在、`masks.ndim==4`、以及 `T/V` 与输入一致。

验收：
- 在 `data/selfcap_bar_8cam60f` 上可跑出 `pseudo_masks.npz + viz/`（产物不入库）

---

## Task A14: 弱融合接入训练（mask-weighted L1，默认关闭）

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- (Optional) Modify: `third_party/FreeTimeGsVanilla/run_pipeline.sh`（若要加 env 快捷入口）
- Create: `scripts/tests/test_weak_fusion_flags.py`（静态检查，避免回归）

设计选择（建议冻结）：
- 只改 `L1`（`lambda_img` 部分），SSIM/LPIPS 保持原样，降低不稳定风险。
- 只在训练前 N steps 启用（例如 `weak_fusion_end_step=2000`），后期自动退回 baseline loss。

新增配置（示例，可按实现微调）：
- `pseudo_mask_npz: Optional[str] = None`
- `pseudo_mask_weight: float = 0.0`（0 即关闭）
- `pseudo_mask_end_step: int = 0`（0 表示不启用）

实现要点：
- 在 trainer 初始化时（或第一次迭代）加载 `pseudo_masks.npz` 并缓存到 CPU/显存（优先 CPU，按需 upsample 到当前 batch H/W）。
- 训练 step 内从 `data["frame_offset"]` 与 `data["camera_idx"]` 取索引，得到 `mask[B,1,H,W]`。
- 权重：`w = 1 + pseudo_mask_weight * mask`，用 `w` 对 `abs(colors-pixels)` 做加权均值（建议除以 `w.mean()` 归一化）。

单测建议：
- `test_weak_fusion_flags.py`：读取 trainer 源码文本，断言出现新参数名（和已有测试风格一致）。

验收：
- 不传 mask 参数时，baseline 行为不变（同命令可跑通）
- 传 mask 参数 + `max_steps=60` 可跑通并产出视频（指标不要求提升）

---

## Task A15: 固化可复现实验入口（Baseline vs Ours-Weak）

**Files:**
- Create: `scripts/run_train_baseline_selfcap.sh`
- Create: `scripts/run_train_ours_weak_selfcap.sh`
- Update: `notes/decision-log.md`（追加 2026-02-24 条目）

要求：
- 两个脚本都只依赖：
  - `data/selfcap_bar_8cam60f`（软链即可）
  - `outputs/`（不入库）
  - `third_party/FreeTimeGsVanilla/.venv`
- 统一默认：
  - `GPU=0`
  - `MAX_STEPS=200`（可用 env 覆盖）
  - `RENDER_TRAJ_PATH=fixed`
- `ours_weak` 脚本额外行为：
  - 若 mask 不存在则先运行 `bash scripts/run_cue_mining.sh ...`
  - 训练时传入 `--pseudo-mask-npz outputs/cue_mining/.../pseudo_masks.npz --pseudo-mask-weight ... --pseudo-mask-end-step ...`

验收：
- 运行两脚本可得到两份 `outputs/<exp>/videos/traj_4d_step*.mp4` + `stats/val_step*.json`
- `scripts/build_report_pack.py` 能识别出两条 run（通过 `dataset/gate` 派生列）

---

## Task A16: 合流与推送（窗口期操作，避免踩踏）

**Files:**
- Modify: 多文件（上述变更）

Step 1: 本分支自检
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-vggt-weak
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_cue_mining_contract.py
$PY scripts/tests/test_weak_fusion_flags.py
bash -n scripts/run_cue_mining.sh
bash -n scripts/run_train_baseline_selfcap.sh
bash -n scripts/run_train_ours_weak_selfcap.sh
```

Step 2: 提交（不包含 data/ 与 outputs/）

Step 3: 合并回 `main`（建议由 A 执行，确保单点集成）

Step 4 (Optional): 若需要协作/多机同步，执行 `git push origin main`
