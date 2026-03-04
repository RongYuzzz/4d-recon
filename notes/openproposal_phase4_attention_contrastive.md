# OpenProposal Phase 4 — VGGT Feature Metric Result (THUman4.0 s00)

Date: 2026-03-04 (UTC)  
Plan: `docs/plans/2026-03-03-openproposal-phase4-vggt-feature-metric.md`  
Scope: local execution + local eval

## 1) Runs And Validity

Baseline (anchor):
- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

First-pass treatment runs (**discarded**, not comparable):
- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600`
- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_lam0.005_600`
- Reason: `cfg.yml` shows `init_npz_path` points to worktree-local path, not the same source as baseline.

Same-init reruns (**valid comparison set**):
- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600_sameinit`
- `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`
- Baseline-consistent `init_npz_path`:
  - `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

## 2) Protocol Footprint (Same-Init Runs)

- `MAX_STEPS=600`
- `VGGT_FEAT_PHI_NAME=token_proj`
- `VGGT_FEAT_LOSS_TYPE=cosine`
- `VGGT_FEAT_GATING=framediff`
- `VGGT_FEAT_GATING_TOP_P=0.10`
- `VGGT_FEAT_EVERY=8`
- `VGGT_FEAT_START_STEP=0`
- `VGGT_FEAT_RAMP_STEPS=400`
- Main run: `LAMBDA_VGGT_FEAT=0.01`
- One-shot iteration: `LAMBDA_VGGT_FEAT=0.005`
- Shared cache:
  - NPZ: `/root/autodl-tmp/projects/4d-recon/outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/gt_cache.npz`
  - Meta: `/root/autodl-tmp/projects/4d-recon/outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/meta.json`
- Masked eval口径:
  - `mask_source=dataset`, `bbox_margin_px=32`, `mask_thr=0.5`
  - snapshot文件：`stats_masked/test_step0599_phase4.json`

## 3) Metrics (Baseline vs Same-Init Only)

Full-frame 来自 `stats/test_step0599.json`，fg-masked 来自 `stats_masked/test_step0599_phase4.json`。

| run | psnr | ssim | lpips | tlpips | psnr_fg | lpips_fg | Δtlpips | Δpsnr_fg | Δlpips_fg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline `planb_init_600` | 16.152018 | 0.562077 | 0.732467 | 0.007053 | 16.806620 | 0.243883 | +0.000000 | +0.000000 | +0.000000 |
| feat `lam=0.01` sameinit | 16.312569 | 0.571112 | 0.731300 | 0.008083 | 16.458392 | 0.255931 | +0.001030 | -0.348228 | +0.012048 |
| feat `lam=0.005` sameinit | 16.304039 | 0.572108 | 0.732396 | 0.007096 | 16.682030 | 0.252479 | +0.000043 | -0.124590 | +0.008596 |

Guardrail (`ΔtLPIPS <= +0.01`):
- `lam=0.01`: `+0.001030` (pass)
- `lam=0.005`: `+0.000043` (pass)

Phase 4 主目标（`psnr_fg ↑` + `lpips_fg ↓`）:
- 两条 same-init run 均未达成：`psnr_fg` 下降、`lpips_fg` 上升。

## 4) Diagnostics / Failure Boundary (Concrete Evidence)

1. **对比口径风险已命中，且已纠正**  
   首轮两条 treatment 的 `init_npz_path` 与 baseline 不同，属于 confounded comparison，已明确弃用；最终结论只看 `*_sameinit`。

2. **Plan-B 初始速度信息为零（时间一致性分支几乎不可用）**  
   从 `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz` 读取：
   - `has_velocity_true = 0 / 92749 (ratio=0.0)`
   - `vel_nonzero = 0 / 92749 (ratio=0.0)`

3. **Triangulation 仅覆盖 frame 0，时序监督先天稀疏**  
   `data/thuman4_subject00_8cam60f/triangulation/` 只有：
   - `points3d_frame000000.npy`
   - `colors_frame000000.npy`
   - `frame_manifest.csv`（仅 frame_idx=0，num_points=382）

4. **训练日志（TB 标量）显示 correspondence loss 全程为 0**  
   在两条 same-init run 的 `tb/events.out.tfevents.*` 中：
   - `loss/corr_raw`: 全 0（nonzero ratio = 0.0）
   - `loss_weighted/corr`: 全 0（nonzero ratio = 0.0）
   - `vggt_feat/active` 有值（8.0），但有效约束主要来自弱 feature 项，且末期趋零。

5. **可解释证据已生成（top-k token temporal match）**  
   - `/root/autodl-tmp/projects/4d-recon/outputs/qualitative_local/openproposal_phase4/tokenproj_topk/token_top30_cam09_frame000000_to_000001.jpg`
   - `/root/autodl-tmp/projects/4d-recon/outputs/qualitative_local/openproposal_phase4/tokenproj_topk/token_top30_cam09_frame000030_to_000031.jpg`

## 5) Final Decision (Phase 4 Stop-Loss)

- 结论：在同口径（same-init）下，Phase 4 的 VGGT feature-metric loss 没有提升 fg 目标指标，属于“full-frame轻微变化但 fg 指标退化”的失败边界。
- Guardrail：`ΔtLPIPS` 未显著恶化，满足约束。
- 按计划止损：Phase 4 不再继续扩参；保留当前失败边界与证据链，交由后续阶段按新假设设计（例如先补可用时序/velocity supervision，再重启 correspondence 类约束）。
