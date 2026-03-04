# OpenProposal — Phase 2 审查报告（VGGT/Diff Pseudomask Mining）

Date: 2026-03-04 (UTC)  
Scope: 审查 `docs/plans/2026-03-03-openproposal-phase2-vggt-pseudomask.md` 的执行质量与可复核性（仅 Phase 2）。

## 0) 审查结论（摘要）

- **总体结论：Phase 2 达标（PASS）**：已在 THUman4.0 s00（8 cams × 60 frames）上产出两套可审计的 `pseudo_masks.npz`（diff vs vggt），并完成 `quality.json` QA、可解释可视化、以及 `miou_fg` health-check（基于 dataset masks 作为 GT）。
- **关键发现（会影响后续 Phase 3/4 的效果预期）**：在默认评测阈值 `mask_thr=0.5` 下，`q0.995` 的 pseudo masks 极度稀疏，`miou_fg` 接近 0（diff=0.0，vggt≈2.67e-6）。Phase 3 若追求 `psnr_fg/lpips_fg` 提升，需要明确采用更低 quantile（如 q0.950）或调整 mask 生成/注入策略。
- **审计风险（文档层需注意）**：Phase 2 的 `miou_*` 快照 JSON 是用 `lpips_backend=dummy` 生成的，因此其中的 `lpips_fg` 不是真实 LPIPS（只应使用 `miou_fg` 字段做 health-check）。

## 1) 目标与口径对齐检查

Phase 2 目标（来自计划）：
- 在 Phase 1 载体上产出 `diff` 与 `vggt` 两套 `pseudo_masks.npz`，并提供 QA（quality + 可视化）与（可选）`miou_fg` 体检，为 Phase 3/4 的 weak/feature-loss 注入做输入。

口径（local-eval only）：
- 输出与可视化全部在本机 `outputs/**`；不提交数据帧/GT mask 到 git/PR/report-pack。
- mask 语义：本阶段输出为 **“foreground/dynamic ROI cue（silhouette-oriented heuristic）”**，不直接等价论文 dynamic-region（除非另有等价证明）。

## 2) 产物与复核点（可复核）

### 2.1 Frozen tags（计划 Task 2 冻结产物）

（均存在 `pseudo_masks.npz + quality.json + viz/grid + viz/overlay` contract）
- diff: `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3`
- vggt: `outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3`

复核要点（本次审查已核对存在性）：
- `.../pseudo_masks.npz` keys: `masks, camera_names, frame_start, num_frames, mask_downscale`
- `.../quality.json` keys: `all_black/all_white/temporal_flicker_l1_mean/...`
- `.../viz/grid_frame000000.jpg` 存在
- `.../viz/overlay_cam02_frame000000.jpg`（legacy alias）存在

### 2.2 QA 结论（计划 Task 3）

来自 `quality.json`（冻结 tag）：
- diff（q0.995）：`all_black=false`, `all_white=false`, `temporal_flicker_l1_mean≈3.27e-4`
- vggt（q0.995）：`all_black=false`, `all_white=false`, `temporal_flicker_l1_mean≈4.93e-4`

额外稀疏性诊断（note 已记录且可复现）：
- 在 `mask_thr=0.5`（即 128/255）口径下 activation 非常稀疏，这是 `miou_fg` 接近 0 的直接原因之一。

### 2.3 可解释可视化（计划 Task 3）

计划要求的“入口图”存在（本机查看，不入库）：
- `.../viz/grid_frame000000.jpg`（diff/vggt 各 1）

额外对照可视化存在（本机）：
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/`（success/failure 示例若干）

### 2.4 `miou_fg` health-check（计划 Task 4）

Anchor run（Phase 1 产物）：
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

快照结果文件（存在且包含 `miou_fg` 字段）：
- diff: `.../stats_masked/test_step0599_miou_diff.json` → `miou_fg=0.0`
- vggt: `.../stats_masked/test_step0599_miou_vggt.json` → `miou_fg≈2.67e-6`

解释边界（必须遵守）：
- 这里的 `gt_fg` 是 THUman4.0 dataset-provided masks（二值化阈值 0.5），不等价“人工实例分割 GT”。
- 这里的 `pred_fg` 是 Phase 2 算法生成 pseudo masks（二值化阈值 0.5）。
- `miou_fg` 仅作为“前景一致性体检”，不应在论文/报告中被表述为“有人工 GT 的分割精度”。

## 3) 执行记录与文档完整性

Phase 2 说明文档齐全：
- `notes/openproposal_phase2_vggt_pseudomask.md`（包含 frozen tags、命令行、语义声明、QA、可视化路径、miou 结果、止损 retune 记录与合规声明）

止损 retunes（计划允许 1–2 次尝试）：
- `q0.990` 与 `q0.950` 的 diff/vggt 目录均存在，作为 Phase 3 的输入备选与对照证据。

## 4) 发现的问题 / 风险与建议

1) **miou 评测命令会覆盖 `stats_masked/test_step0599.json`（计划层 footgun）**
   - Phase 2 计划的 Task 4 通过 evaluator 写入固定路径，然后再 `cp` 出快照；若不做备份/恢复，会污染 Phase 1 的 masked 基准文件，导致后续 Phase 指标表被“dummy LPIPS”混入。
   - 建议：像 Phase 5 一样在 Task 4 增加 `backup -> run -> snapshot -> restore`（防踩坑）。

2) **`miou_*` JSON 中的 `lpips_fg` 值不可解释**
   - 计划命令使用 `lpips_backend=dummy`，所以 `lpips_fg` 是 L1 proxy，不可与真实 LPIPS 混用。
   - 建议：后续审阅/写报告时仅引用 `miou_fg` 字段；或在 evaluator 输出里增加 `lpips_backend` 字段以消除歧义。

3) **冻结 tag（q0.995）“可审计”但对后续增益不乐观**
   - 冻结输出满足交付，但其稀疏性导致 `mask_thr=0.5` 下的 `miou_fg≈0`。
   - 若 Phase 3/4 以 `psnr_fg/lpips_fg` 为主目标，需要明确采用 retune 版本（例如 q0.950 diff-invert）并在 Phase 3 文档里写死输入 tag，避免跨 Phase 追溯困难。

4) **scripts/tests 下的 cue_mining contract 是“可执行脚本”而非 pytest 测试**
   - `scripts/tests/test_cue_mining_contract.py` / `test_cue_mining_quality_stats.py` 目前需手动 `python3` 运行，`pytest -q` 不会覆盖。
   - 这是“可用但易漏”的风险；建议后续改为 pytest `def test_*` 形式或在 CI/说明中显式加入运行命令。

## 5) Phase 2 审查 Gate Verdict

- 输出 contract（npz+quality+viz）：PASS
- 语义声明与合规（local-eval only）：PASS
- QA（非全黑/全白、flicker 可控）：PASS
- miou health-check（可复核且解释边界清晰）：PASS（结果接近 0 作为关键发现保留）

## 6) 建议的下一步（进入 Phase 3 审查前）

- Phase 3 审查重点：确认实际注入使用的 mask tag（q0.950 vs q0.995）在文档/命令里被“写死”，并核对其与 masked evaluator 口径（mask_thr/bbox_margin/fill-black）一致。

