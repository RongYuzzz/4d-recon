# OpenProposal — Phase 1 审查报告（THUman4.0 Dataset + Masked Metrics）

Date: 2026-03-04 (UTC)  
Scope: 审查 `docs/plans/2026-03-03-openproposal-phase1-dataset-metrics.md` 的执行质量与可复核性（仅 Phase 1）。

## 0) 审查结论（摘要）

- **总体结论：Phase 1 达标（PASS）**：已跑通 “THUman4.0 子集适配 → sparse/0 → triangulation → 训练 smoke600 → fg-masked 指标落盘” 的闭环，并且后续 Phase 2–5 已在此载体上实际推进，说明载体可用。
- **关键风险已识别并修复（文档层）**：Phase 1 note 中 `lpips_fg` 数值与实际落盘 JSON 不一致、runbook 的 `camera_ids` 模板与真实 THUman4.0 `camXX` 命名不一致、以及 `lpips_backend=auto` 在系统 Python 下不可用导致复现命令易失败（已补 doc 修复）。
- **仍然存在的工程风险（待决定是否修复）**：`scripts/thuman4_inventory.py` 当前按字典序选择相机，默认会选到 `cam00`；但 `cam00` 在本机前 60 帧存在缺帧，会导致 adapter 失败。现已在 runbook 中写死推荐相机列表（`cam01..cam08`），但脚本本身仍是“易踩坑”。

## 1) 目标与口径对齐检查

Phase 1 目标（来自计划）：
- 在 THUman4.0 小子集上完成可复核闭环：数据适配 → COLMAP/sparse → triangulation → 训练 smoke → fg-masked 指标（PSNR/LPIPS）。

口径（写死并已复核）：
- **local-eval only**：不提交 `data/`、`outputs/`；不把 GT 帧/mask 写进 `docs/report_pack/**`。
- fg-masked ROI：`mask -> bbox crop (+margin=32) -> fill-black outside mask -> metric`（见 `docs/protocols/protocol_v3_openproposal.yaml`）。
- mask：使用 THUman4.0 dataset-provided masks（adapter 输出到 `data/.../masks/<cam>/<frame>.png`），二值阈值 `mask_thr=0.5`。

## 2) Repo 级交付物（可复核）

### 2.1 协议与说明文档

- `docs/protocols/protocol_v3_openproposal.yaml`：v3 协议骨架齐全（数据、相机拆分、masked eval 口径）。
- `notes/openproposal_phase1_colmap_runbook.md`：COLMAP sparse/0 + triangulation 的命令 runbook。
- `notes/openproposal_phase1_dataset_and_metrics.md`：Phase 1 总结 note（合规、口径、gate 状态与关键路径）。
- `notes/openproposal_phase1_thuman4_runbook.md`：Phase 1 一键命令 runbook（commands only）。

### 2.2 代码与合约测试（TDD）

- Adapter：
  - `scripts/adapt_thuman4_release_to_freetime.py`
  - `scripts/tests/test_adapt_thuman4_release_contract.py`
- Masked evaluator：
  - `scripts/eval_masked_metrics.py`
  - `scripts/tests/test_eval_masked_metrics_contract.py`

本次审查复跑（PASS）：
- `pytest -q scripts/tests/test_adapt_thuman4_release_contract.py scripts/tests/test_eval_masked_metrics_contract.py` → `2 passed`

## 3) 本机数据与产物（local-only evidence）

> 说明：以下为本机路径存在性/一致性审查，**不进入 git**。

### 3.1 THUman4.0 raw 与适配后数据

- raw（本机）：`data/raw/thuman4/subject00/{images,masks}/cam00..cam09`
- 适配后数据（8 cams × 60 frames）：`data/thuman4_subject00_8cam60f`
  - `images/`：480 张（`02..09` 每相机 60）
  - `masks/`：480 张（`02..09` 每相机 60）
  - 适配记录：`data/thuman4_subject00_8cam60f/adapt_scene.json`（确认使用 `cam01..cam08 -> 02..09`）

### 3.2 COLMAP sparse/0 与 triangulation

- sparse：`data/thuman4_subject00_8cam60f/sparse/0/{cameras.bin,images.bin,points3D.bin}` 存在
- triangulation（smoke）：`data/thuman4_subject00_8cam60f/triangulation/points3d_frame000000.npy` 存在
  - 备注：当前为 “reference sparse + visible_per_frame” 的 smoke 产物，通常只覆盖极少帧（此处为 frame000000），符合 Phase 1 “先跑通闭环、不过度追求全覆盖” 的止损原则。

### 3.3 训练 smoke600 与 masked 评测落盘

- anchor run：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
  - trainer stats：`.../stats/test_step0599.json`（`psnr/ssim/lpips/tlpips`）
  - renders：`.../renders/test_step599_*.png`（计数=60）
  - masked stats：`.../stats_masked/test_step0599.json`（`psnr_fg/lpips_fg/num_fg_frames`）

## 4) 发现的问题与修复记录

### 4.1 Phase 1 note 与实际 masked JSON 数值不一致（已修复）

- 现状：`notes/openproposal_phase1_dataset_and_metrics.md` 里曾记录 `lpips_fg≈0.049`，但实际落盘
  `outputs/.../stats_masked/test_step0599.json` 为 `lpips_fg≈0.244`。
- 根因：`scripts/eval_masked_metrics.py` 支持 `lpips_backend=dummy`（L1 proxy）与 `auto`（真实 LPIPS）。
  dummy 的量纲与真实 LPIPS 不可比，且 Phase 2 的 `miou_fg` 体检快照里确实出现过 dummy 值。
- 修复：已在 `notes/openproposal_phase1_dataset_and_metrics.md` 明确 backend 说明，并把 Phase 1 gate 的
  `lpips_fg` 对齐到当前 anchor run 的真实落盘值（`lpips_backend=auto`）。

### 4.2 Phase 1 runbook 的 `camera_ids` 模板与真实 THUman 命名不一致（已修复）

- 现状：`notes/openproposal_phase1_thuman4_runbook.md` 中曾出现 `camera_ids="000,001,..."`
  的模板，容易误导。
- 修复：已改为明确的 THUman 真实目录名：`cam01..cam08`（并提醒避开 `cam00` 缺帧问题）。

### 4.3 `lpips_backend=auto` 的复现命令在系统 Python 下易失败（已修复）

- 现状：系统 `python3` 不一定安装 `lpips`；直接 `--lpips_backend auto` 会报错。
- 修复：已在 `notes/openproposal_phase1_thuman4_runbook.md` 增加 venv/后备逻辑：
  - 若 `VENV_PYTHON` 可 import lpips → 用 `auto`
  - 否则降级到 `dummy`（仅用于跑通/合约，不与真实 LPIPS 混用）

### 4.4 `scripts/thuman4_inventory.py` 默认可能选到 `cam00`（未修复，已规避）

- 风险：inventory 当前按字典序取前 N 个相机，默认会包含 `cam00`；但 `cam00` 在本机前 60 帧缺帧，
  会导致 adapter 失败。
- 现阶段规避策略：runbook 已写死推荐 `cam01..cam08`，并在 inventory 步骤要求人工确认 `picked_cameras`。
- 是否要代码层修复：建议在后续统一处理（例如在 inventory 增加 “完整帧检查/跳过缺帧 cam” 模式），避免后续复现踩坑。

## 5) Phase 1 审查 Gate Verdict

- 可复核闭环：PASS
- 合规（local-eval only）：PASS
- 口径一致性（masked eval 口径/相机拆分/阈值）：PASS（已补齐 backend 说明）
- 对后续 Phase 支撑：PASS（Phase 2–5 已在此载体上推进）

## 6) 建议的下一步（Phase 2 审查前）

- 在 Phase 2 审查中重点检查：pseudo mask 的来源声明、q/阈值止损过程、以及 `miou_fg` 的“体检解释”是否避免误用（不要把它当作人工实例分割 GT）。

