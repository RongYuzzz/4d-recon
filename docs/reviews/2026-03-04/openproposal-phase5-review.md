# OpenProposal — Phase 5 审查报告（Edit Demo / Removal + Optional mIoU）

Date: 2026-03-04 (UTC)  
Scope: 审查 `docs/plans/2026-03-03-openproposal-phase5-edit-demo-miou.md` 的执行质量与可复核性（仅 Phase 5）。

## 0) 审查结论（摘要）

- **总体结论：Phase 5 达标（PASS）**：已交付一个可播放的 removal/edit demo（static-only / dynamic-only / side-by-side），并给出可解释的速度阈值选择过程（基于 ckpt 的 `||v||` 分布与 keep-ratio 预检）。可选 `miou_fg` 已实现并落盘，且来源口径声明完整。
- **关键发现（与 Phase 2/3 一致）**：`miou_fg=0.0`（dataset masks vs Phase 2 pseudo masks，阈值 0.5），本质反映当前 pseudo masks 在该口径下过稀疏/不对齐；应作为健康检查结论，而不是“分割精度”。
- **工程稳定性处理正确**：考虑到 Plan‑B init 中 `velocities=0` 的历史坑，本 Phase 明确以 **ckpt learned velocities** 做阈值统计与选择，避免了“拿 init 的 p50/p90 做 velocity-filter”导致的无效 demo。

## 1) 目标与口径对齐检查

Phase 5 目标（来自计划）：
- 交付一个可演示的“动静解耦/移除（removal）”闭环；
- （可选）在 dataset masks 存在时提供 `miou_fg`（二值前景）作为定量补充；
- limitation 写死：removal 是 filtering 不是 inpainting（遮挡/背景不可见 → 可能出现洞/残影）。

口径与合规：
- local-eval only：不提交 `data/`、`outputs/`；定性视频只留在 `outputs/qualitative_local/**`。
- velocity split：使用 ckpt 的 `splats.velocities`（`||v||`）并选定阈值 `tau_final`。
- `miou_fg`：`gt_fg` 为 THUman4.0 dataset-provided masks（二值阈值 `mask_thr=0.5`）；`pred_fg` 为 Phase 2 pseudo masks（二值阈值相同）；仅作为一致性 health-check。

## 2) 关键产物与复核点（local-only evidence）

### 2.1 Gate（ckpt）

- 选定 ckpt：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt`（存在）

### 2.2 速度统计与阈值选择（可解释）

- 速度统计报告：`notes/openproposal_phase5_velocity_stats_planb_init_600.md`
- 阈值与理由：`notes/openproposal_phase5_edit_demo.md`（`tau_final=0.070611`，来自 `p50(||v||_ckpt)`）
- keep-ratio 预检（复核）：在 `tau_final=0.070611` 下静/动分割约 50/50，避免 “removed all Gaussians”。

### 2.3 Removal demo（三段视频）

静态（static-only）：
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_static_planb_init_600_tau0.070611/videos/traj_4d_step599.mp4`

动态（dynamic-only）：
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/export_dynamic_planb_init_600_tau0.070611/videos/traj_4d_step599.mp4`

对照（side-by-side）：
- `outputs/qualitative_local/openproposal_phase5/static_vs_dynamic_planb_init_600_tau0.070611.mp4`

本次审查复核：
- 三个文件均存在、可解码（ffprobe 读取正常），且三者 SHA256 不同（不是误拷贝同一视频）。

### 2.4 可选 `miou_fg`（health-check）

- 产物：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_miou_phase5.json`
- 结果：`miou_fg = 0.0`（`mask_source=dataset`, `mask_thr=0.5`, `bbox_margin_px=32`）
- 基准文件保护：存在 `.../test_step0599_before_phase5_miou.json`，且与恢复后的 `.../test_step0599.json` SHA256 一致（避免覆盖污染）。

## 3) 发现的问题 / 风险与建议

1) **export-only 结果目录缺少 `cfg.yml` / `stats/*.json`**
   - 现状：`export_static_*`/`export_dynamic_*` 下 `stats/` 与 `ckpts/` 为空、无 `cfg.yml`（仅有视频与 tb events）。
   - 影响：审计时更依赖“外部 note + ckpt 推导的 kept 计数”而非 result_dir 自带配置快照。
   - 建议（可选）：后续若要增强可审计性，可在 export-only 流程中额外保存一份 `cfg.yml`（或保存 stdout log）到 result_dir（不阻塞本阶段验收）。

2) **环境坑：`Ninja is required to load C++ extensions`**
   - 计划已加入 `PATH="$(dirname "$VENV_PYTHON"):$PATH"` 以确保能找到 `ninja`；执行 note 中也已写明该处理。

## 4) Phase 5 审查 Gate Verdict

- removal demo 可播放 + 有对照：PASS
- tau 选择过程可解释且可复核：PASS
- （可选）`miou_fg` 口径声明完整且不污染基准：PASS
- limitation 写死：PASS

