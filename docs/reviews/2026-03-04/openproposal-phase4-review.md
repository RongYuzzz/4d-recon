# OpenProposal — Phase 4 审查报告（VGGT Feature Metric / Correspondence Loss）

Date: 2026-03-04 (UTC)  
Scope: 审查 `docs/plans/2026-03-03-openproposal-phase4-vggt-feature-metric.md` 的执行质量与可复核性（仅 Phase 4）。

## 0) 审查结论（摘要）

- **总体结论：Phase 4 达标（PASS，作为“失败边界交付”）**：在 THUman4.0 s00 上完成了 Plan‑B + VGGT feature-metric loss 的落地、same-init 公平性 gate、一次迭代、masked eval + guardrail、以及可解释的 top‑k token 可视化。虽然 **未提升** 目标前景指标（`psnr_fg` 未升且 `lpips_fg` 未降），但已按计划止损并形成可审计的 failure boundary + 诊断记录。
- **A/B 公平性处理正确**：首轮 treatment 因 `init_npz_path` worktree-local 而 confounded（无效对照），已明确弃用；最终只采用 `*_sameinit` runs 与 baseline 对比，结论可信。
- **Feature loss 实际生效（非“跑了但没算”）**：TB 标量中 `loss_weighted/feat` 在 step 200/400 为非零（符合 `vggt_feat_every=8` 与 `tb_every=50` 的日志采样规律），证明 feature loss 被执行且参与 total loss。
- **Correspondence loss=0 属于预期**：本 Phase 未启用 temporal correspondence（`lambda_corr=0`），因此 `loss_weighted/corr` 全 0 不是 bug。

## 1) 目标与口径对齐检查

Phase 4 目标（来自计划）：
- 落地 “VGGT feature/correspondence 约束”，尽可能提升 PSNR/LPIPS，**优先 fg-masked (`psnr_fg/lpips_fg`)**；若不提升，需产出可解释 failure boundary + 排查记录，并止损。

评测口径：
- masked eval：`mask -> bbox crop (+margin=32) -> fill-black outside mask -> metric`
- `mask_source=dataset`（THUman4.0 dataset-provided masks）
- `mask_thr=0.5`
- LPIPS backend：`lpips_backend=auto`（真实 LPIPS；FreeTimeGsVanilla venv）
- guardrail：`ΔtLPIPS <= +0.01`（软性但必须记录）

合规（local-eval only）：
- 不提交 `data/`、`outputs/`；可解释图与视频仅保留在 `outputs/qualitative_local/**`。

## 2) 关键产物与复核点（local-only evidence）

### 2.1 Runs（same-init 有效对照集）

根目录：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/`

- baseline：`planb_init_600`
- treatment‑1：`planb_feat_v2_gatediff0.10_600_sameinit`（`lambda_vggt_feat=0.01`）
- treatment‑2：`planb_feat_v2_gatediff0.10_lam0.005_600_sameinit`（一次迭代，仅改 `lambda_vggt_feat=0.005`）

每条 run 的可复核产物（本次审查已核对存在性）：
- `cfg.yml`
- `stats/test_step0599.json`
- `stats_masked/test_step0599_phase4.json`（snapshot）

无效对照（已弃用）：
- `planb_feat_v2_gatediff0.10_600`
- `planb_feat_v2_gatediff0.10_lam0.005_600`
原因：`init_npz_path` 指向 worktree-local 绝对路径，未满足 same-init 公平性 gate。

### 2.2 VGGT cache（预计算产物）

- cache dir：`outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10`
- `gt_cache.npz` 与 `meta.json` 均存在，meta 记录：
  - `phi_name=token_proj`, `token_layer_idx=17`, `token_proj_dim=32`, `phi_shape=(60,8,32,8,9)`
  - `has_gate_framediff=true`, `framediff_top_p=0.1`

### 2.3 可解释可视化（top‑k token temporal match）

- `outputs/qualitative_local/openproposal_phase4/tokenproj_topk/token_top30_cam09_frame000000_to_000001.jpg`
- `outputs/qualitative_local/openproposal_phase4/tokenproj_topk/token_top30_cam09_frame000030_to_000031.jpg`

## 3) 指标复核（从落盘 JSON 读取）

Full-frame（`stats/test_step0599.json`）：
- baseline：PSNR 16.1520 / SSIM 0.5621 / LPIPS 0.7325 / tLPIPS 0.007053
- treat‑1：PSNR 16.3126 / SSIM 0.5711 / LPIPS 0.7313 / tLPIPS 0.008083
- treat‑2：PSNR 16.3040 / SSIM 0.5721 / LPIPS 0.7324 / tLPIPS 0.007096

Guardrail（ΔtLPIPS = treat - baseline）：
- treat‑1：`+0.001030` → PASS
- treat‑2：`+0.000043` → PASS

Foreground-masked（`stats_masked/test_step0599_phase4.json`）：
- baseline：PSNR_FG 16.8066 / LPIPS_FG 0.2439
- treat‑1：PSNR_FG 16.4584 / LPIPS_FG 0.2559
- treat‑2：PSNR_FG 16.6820 / LPIPS_FG 0.2525

结论：
- Phase 4 主目标（`psnr_fg ↑` 且 `lpips_fg ↓`）**未达成**（两条 treatment 均 FG 退化）。

## 4) 有效性与诊断复核

### 4.1 Same-init 公平性 gate（PASS）

- baseline 与两条 `*_sameinit` 的 `init_npz_path` 完全一致：
  - `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

### 4.2 Feature loss 是否真正参与优化（PASS）

- TB 标量存在：`loss/feat_raw`、`loss_weighted/feat`、`vggt_feat/active`
- 由于 `vggt_feat_every=8` 且 `tb_every=50`，在 TB 标量里能看到非零值的 step 主要出现在 200 的倍数（LCM=200），这是预期采样现象，不应误判为“feature loss 长期为 0”。
- 在 `planb_feat_v2_gatediff0.10_600_sameinit` 中，`loss_weighted/feat` 在 step 200/400 为非零（约 `0.005353`/`0.009250`），证明 loss 生效且加入 total loss。

### 4.3 Correspondence loss=0（PASS，预期）

- `lambda_corr=0` 且未提供 `temporal_corr_npz`，因此 `loss_weighted/corr` 全程为 0 属于预期，不作为失败证据。

## 5) 发现的问题 / 风险与修复

1) **首轮 treatment confounded（已处理）**
   - `init_npz_path` worktree-local 导致对照无效；
   - 处理：明确弃用，并重跑 `*_sameinit`（有效对照集）。

2) **日志解读风险：TB 里 feature loss 末期显示为 0 并不代表趋零（已修复说明）**
   - 根因：feature loss 只在 `step % vggt_feat_every == 0` 计算，而 TB 只在 `step % tb_every == 0` 记录；
   - 处理：已在 `notes/openproposal_phase4_attention_contrastive.md` 写明该采样规律与非零 step，避免误读。

3) **masked evaluator 输出缺少 `lpips_backend` 字段（未修复代码，已在 note 记录）**
   - 风险：后续汇总表格时可能把 dummy 与 real LPIPS 混用；
   - 现阶段缓解：Phase 4 note 已显式记录本次 `lpips_backend=auto`。

## 6) Phase 4 审查 Gate Verdict

- feature-loss 跑通 + cache 可复核：PASS
- same-init 公平性：PASS（无效对照已弃用）
- masked eval + guardrail：PASS（尽管 FG 指标未提升）
- failure boundary + 止损执行：PASS

