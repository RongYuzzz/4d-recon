# VGGT Feature Metric Loss V1 Implementation Plan (Owner B)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变 `protocol_v1`（数据/帧段/相机划分/关键超参冻结）的前提下，实现 “VGGT feature-level prior” 的最小可用版本（feature metric loss），并在 SelfCap bar canonical 数据上完成 baseline/control/feature-loss 的可审计对比结论。

**Architecture:** 采用 “离线缓存 GT 特征 + 训练时对 render 计算特征” 的闭环：  
1) 先对 GT 图像离线预计算 VGGT 输出（作为 `phi(I_gt)`），存入可索引的 cache；  
2) 训练时以低频、低分辨率、可选 patch 采样方式，对 render 图像计算 VGGT 输出（作为 `phi(I_render)`，允许对输入求梯度但冻结 VGGT 权重）；  
3) 增加 `L_feat = ||phi(I_render) - phi(I_gt)||`（可按 conf 加权/可选 dynamic gating），以提升时序稳定性（优先 tLPIPS）。

**Tech Stack:** PyTorch、`vggt`（HF `facebook/VGGT-1B`）、现有 trainer `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`、脚本级测试 `scripts/tests/*.py`、协议 v1 运行脚本（参考 `scripts/run_train_*_selfcap.sh`）。

---

### Task B30: 创建隔离 Worktree

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260224-vggt-feature-loss-v1 .worktrees/owner-b-20260224-vggt-feature-loss-v1 main
git -C .worktrees/owner-b-20260224-vggt-feature-loss-v1 status --porcelain=v1
```

Expected:
- worktree 干净。

---

### Task B31: 记录/核验 VGGT 可用性（确保主线不被环境拖死）

**Files:**
- Update: `notes/vggt_setup.md`（若有新增依赖/权重路径/性能数据）

**Step 1: 在 canonical 数据上跑一次 vggt backend smoke（只做 health check）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1
export HF_HUB_OFFLINE=1
export HF_HUB_DISABLE_XET=1
GPU=1 OUT_DIR=outputs/cue_mining/selfcap_bar_8cam60f_vggt_healthcheck \
  bash scripts/run_cue_mining.sh data/selfcap_bar_8cam60f selfcap_bar_8cam60f_vggt_healthcheck 0 2 vggt 4
```

Expected:
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_healthcheck/pseudo_masks.npz` 存在。

---

### Task B32: 增加 GT VGGT 输出离线缓存脚本（cache 契约先行）

**Files:**
- Create: `scripts/precompute_vggt_cache.py`
- Create: `scripts/tests/test_vggt_cache_contract.py`
- Update: `notes/vggt_setup.md`（补充 cache 生成命令与开销）

**Cache 目标（v1 最小集）：**
- 每个 (cam, frame) 需要可索引的 GT “特征”与 meta。
- 建议先选 VGGT 的 `depth`/`world_points` 之一作为 `phi()`（二选一即可，后续可扩展）：
  - `phi=depth`：更轻，适合先验证 tLPIPS 叙事
  - `phi=world_points`：信息更足，但可能更重

**Step 1: 写脚本级 failing test（不依赖真实 VGGT，先用 dummy backend 走通契约）**
- 在 `scripts/precompute_vggt_cache.py` 支持 `--backend dummy`：
  - dummy 输出：对输入 RGB 做固定下采样，生成 shape 可控的 `phi`（用于单测）。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1
python3 scripts/tests/test_vggt_cache_contract.py
```
Expected:
- FAIL（缺少脚本/CLI 或输出契约不满足）。

**Step 2: 实现最小 cache 生成（dummy backend）**
- 输出目录建议：
  - `outputs/vggt_cache/<tag>/`
- 必须产物：
  - `gt_cache.npz`
  - `meta.json`
- `gt_cache.npz` 建议 keys：
  - `phi`: float16/float32，shape `[T,V,C,Hf,Wf]`（T=num_frames，V=len(camera_names)）
  - `camera_names`: `str[V]`
  - `frame_start`: int
  - `num_frames`: int
  - `phi_name`: str（例如 `depth` / `world_points` / `dummy_rgb`）
  - `vggt_mode`: str（`crop`/`pad`，必须写入）
  - `input_size`: `[H_in,W_in]`（VGGT preprocess 后的尺寸，比如 518x518）
  - `phi_size`: `[Hf,Wf]`

**Step 3: 让测试转绿**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1
python3 scripts/tests/test_vggt_cache_contract.py
```
Expected:
- PASS。

**Step 4: 接入真实 VGGT backend（并保持 dummy 可用于测试）**
- `--backend vggt`：读取 `data_dir/images/<cam>/<frame>.jpg`，用 VGGT forward 得到 `phi`（depth 或 world_points）
- 必须支持：
  - `--camera_ids 02,03,...`
  - `--frame_start / --num_frames`
  - `--vggt_model_id` / `--vggt_cache_dir` / `--vggt_mode`
  - `--phi_name depth|world_points`
  - `--phi_downscale`（把 518x518 下采样到更小，降低 I/O）

**Step 5: commit**

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1
git add scripts/precompute_vggt_cache.py scripts/tests/test_vggt_cache_contract.py notes/vggt_setup.md
git commit -m "feat(vggt): add GT cache precompute script and contract test"
```

---

### Task B33: 训练时注入 feature metric loss（确保梯度回到 render->gaussians）

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Create: `scripts/tests/test_vggt_feature_loss_flags.py`

**Step 1: 新增 config flags（默认关闭，不影响 baseline）**
- 新增：
  - `vggt_feat_cache_npz: str = ""`
  - `lambda_vggt_feat: float = 0.0`
  - `vggt_feat_start_step: int = 0`（warmup）
  - `vggt_feat_every: int = 1`（低频触发，建议默认 4 或 8）
  - `vggt_feat_phi_name: str = "depth"`（与 cache 对齐）
  - `vggt_feat_patch_k: int = 0`（0 表示先做全图/或全图下采样；>0 表示 patch 采样）
  - `vggt_feat_patch_hw: int = 32`（patch 尺寸，按 `phi` 空间）
  - `vggt_feat_use_conf: bool = True`（若 cache 含 conf，按 conf 加权）
  - `vggt_feat_gating: str = "none"`（`none|framediff|cue`，先实现 `none`）
- 脚本级测试断言这些 flags 存在（避免回归删掉）。

**Step 2: cache 加载（一次性）**
- 当 `lambda_vggt_feat>0` 且 `vggt_feat_cache_npz` 非空时加载：
  - 读取 `phi[T,V,C,Hf,Wf]` 与 meta；
  - 建立 `camera_name -> view_index` 的映射；
  - 校验 `frame_start/num_frames` 与训练的 `[start_frame,end_frame)` 一致或可安全对齐。

**Step 3: render 的 VGGT 预处理（不走 PIL，不落盘）**
- 目标：把 `colors[b]`（float32，[H,W,3]）转成与 cache 一致的 `phi` 空间分辨率。
- v1 建议：
  - 直接把 render resize 到 `input_size`（518x518）并做 crop/pad 的等价操作（与 `vggt.utils.load_fn.load_and_preprocess_images` 对齐）
  - 再喂给 VGGT 得到 `phi_render`

**关键约束（必须写在代码注释里，避免踩坑）：**
- 对 render 计算 `phi_render` 时 **不能使用 `torch.no_grad()`**，否则梯度不会回传到 gaussians。
- 需要冻结 VGGT 权重（`requires_grad_(False)`），但允许对输入求梯度（让 loss 作用于 render->gaussians）。

**Step 4: feature loss 计算（v1 先做最小可用）**
- 触发条件：
  - `lambda_vggt_feat>0`
  - `step >= vggt_feat_start_step`
  - `step % vggt_feat_every == 0`
- loss：
  - `L_feat = mean(|phi_render - phi_gt|)` 或 L2（二选一即可）
  - 若有 conf：按 `conf_gt` 或 `min(conf_gt, conf_render)` 加权
- 把 `lambda_vggt_feat * L_feat` 加入总 loss，并在日志里打印 `feat_loss`。

**Step 5: commit**

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-vggt-feature-loss-v1
git add third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py scripts/tests/test_vggt_feature_loss_flags.py
git commit -m "feat(trainer): add optional VGGT feature metric loss (frozen model)"
```

---

### Task B34: 新增可复现 runner（protocol v1：feature_loss_v1）

**Files:**
- Create: `scripts/run_train_feature_loss_selfcap.sh`
- (Optional) Update: `README.md`（新增一条 feature_loss_v1 命令）

Runner 约束：
- 默认路径与 split 对齐 `docs/protocol.yaml`（与 `scripts/run_train_baseline_selfcap.sh` 一致）
- 若 cache 不存在，自动先跑 `scripts/precompute_vggt_cache.py`（只生成一次，可复用）
- 产物目录建议：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_600`
  - gated 版本：
    - `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v1_gated_600`

---

### Task B35: 实验与止损（严格按 protocol v1 口径写结论）

**Runs (GPU1):**
- 先 short sanity（200 steps）验证：
  - 训练不崩
  - 吞吐下降可接受（<2x，若超限需调大 `vggt_feat_every` / 降低分辨率 / patch）
- 再 full600：
  - baseline（已存在，不重跑）
  - control（已存在，不重跑）
  - feature_loss_v1_600（新）
  - feature_loss_v1_gated_600（可选加分项，若 gating 实现已就绪）

**成功线（满足任一条即可视为 “有趋势”）：**
- tLPIPS 下降 ≥ 10%
- 或 LPIPS 下降 ≥ 0.01
- 或 PSNR +0.2 dB

**止损线：**
- 训练明显不稳（loss 爆、render 更闪）
- 或吞吐下降 >2x 且无法通过 `every/patch/downscale` 控住
- 或 2 次 full run 都无任何正向趋势

**交付：**
- Update: `notes/feature_loss_v1_attempt.md`（写清 cache tag、flags、吞吐、指标与失败分析）

