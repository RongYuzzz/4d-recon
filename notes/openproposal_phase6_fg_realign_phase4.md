# Phase 6 FG realign - Phase 4 follow-up (VGGT feature loss)

Date: 2026-03-05

## Run list (same-init fairness check)

- baseline: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
- treatment A (`gating=none`, ds4 cache):
  `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit_r1`
- treatment B (`gating=none`, ds2 cache):
  `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`

All three `cfg.yml` have identical `init_npz_path`:

- `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

## Cache meta summary

- ds4 cache: `/root/autodl-tmp/projects/4d-recon/outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/meta.json`
  - `phi_size=[8, 9]` (72 tokens)
  - cache file includes framediff gate metadata (`has_gate_framediff=True`), but training used `VGGT_FEAT_GATING=none`
- ds2 cache: `/root/autodl-tmp/projects/4d-recon/outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds2_nogate/meta.json`
  - `phi_size=[16, 18]` (288 tokens)
  - `has_gate_framediff=False`

TB active checks (exported csv):

- ds4 run `vggt_feat/active` at steps 0/200/400: `72/72/72`
- ds2 run `vggt_feat/active` at steps 0/200/400: `288/288/288`

## Metrics @ step 599

| run | psnr | lpips | tlpips | psnr_fg | lpips_fg | psnr_fg_area | lpips_fg_comp |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 16.1520 | 0.7325 | 0.007053 | 16.8066 | 0.24388 | 9.8674 | 0.04960 |
| feat_nogate_ds4_r1 | 16.1570 | 0.7314 | 0.007293 | 16.6825 | 0.24208 | 9.7433 | 0.05062 |
| feat_nogate_ds2_r1 | 16.1195 | 0.7367 | 0.007025 | 16.5078 | 0.24835 | 9.5686 | 0.05087 |

Guardrail check (`ΔtLPIPS <= +0.01`, vs baseline):

- feat_nogate_ds4_r1: `+0.000240` (PASS)
- feat_nogate_ds2_r1: `-0.000028` (PASS)

## Outcome and next-step suggestion

- `gating=none` 激活数量符合预期（72/288），说明监督路径确实被打开。
- 但在前景指标上，两个 treatment 都未优于 baseline：
  - ds4: `psnr_fg` 与 `psnr_fg_area` 下降；`lpips_fg` 微降但 `lpips_fg_comp` 变差。
  - ds2: 前景与全帧 `lpips` 均明显变差。
- 当前结论倾向于 **Phase 4 止损**（至少在 `lambda=0.005, cosine, token_proj` 组合下），优先回到 Phase 3 中更有前景的方向做更细的权重/日程扫描。

