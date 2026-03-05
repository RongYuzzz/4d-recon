# OpenProposal — Pre‑Expert Seed Replication 审查报告（weak `staticp99 + w0.8`）

Date: 2026-03-05 (UTC)  
Scope: 审查计划 `docs/plans/2026-03-05-openproposal-preexpert-seedrep-staticp99.md` 的执行质量、可复核性与结论（THUman4.0 s00，local-only eval）。

## 0) 审查结论（摘要）

- **执行闭环：PASS**。Task 0–6 已完成；4 个 600-step run（baseline/treatment × 2 seeds）均产出 `stats/test_step0599.json` 与 `stats_masked/test_step0599.json`；same-init gate 满足（`init_npz_path` 一致）。
- **科学结论：FAIL（不稳定）**。按严格 gate `psnr_fg↑ 且 lpips_fg↓`（并满足 `ΔtLPIPS<=+0.01`），两 seed 中仅 1 个通过：`OVERALL_OK=False`。该设置属于 **seed-sensitive**，不宜作为“稳定有效”结论对外宣称。
- **可审计记录：PASS**。已将 run 路径、输入 hash、评测口径、逐 seed deltas 与最终 verdict 写入 `notes/openproposal_preexpert_seedrep_staticp99.md`。

## 1) 复核依据（产物与口径）

计划：
- `docs/plans/2026-03-05-openproposal-preexpert-seedrep-staticp99.md`

审计 note（唯一事实源）：
- `notes/openproposal_preexpert_seedrep_staticp99.md`

锁定输入（note 中已记录 sha256）：
- Plan‑B init：`outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- weak mask：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`

训练与评测口径（note 中已写死）：
- budget：`MAX_STEPS=600`，比较点 `step=599`
- eval：`scripts/eval_masked_metrics.py --mask_source dataset --bbox_margin_px 32 --mask_thr 0.5`
- guardrail：`ΔtLPIPS <= +0.01`

## 2) Task-by-Task 完成度审查

### Task 0–4（Gate / 4 runs / masked eval）：PASS

复核点：
- 4 个 result_dir 都存在：
  - `_seedrep_planb_init_600_seed43`
  - `_seedrep_weak_staticp99_w0.8_600_seed43`
  - `_seedrep_planb_init_600_seed44`
  - `_seedrep_weak_staticp99_w0.8_600_seed44`
- 四者的 `cfg.yml` 中：
  - baseline 的 `pseudo_mask_weight=0` 且 treatment 为 `0.8`
  - baseline 与同 seed treatment 的 `init_npz_path` 相同（same-init fairness）
- 四者的 `stats_masked/test_step0599.json` 均存在，且 `num_fg_frames=60`（ROI 非空）

### Task 5（两 seed verdict）：PASS（结论为不稳定）

逐 seed 结论（直接引用 note）：
- seed43：`Δpsnr_fg=+1.619054`、`Δlpips_fg=-0.017309`、`ΔtLPIPS=+0.000795` → **OK**
- seed44：`Δpsnr_fg=+0.280750`、`Δlpips_fg=+0.000248`、`ΔtLPIPS=+0.001401` → **FG fails**

最终：
- `OVERALL_OK=False`

### Task 6（审计记录）：PASS

- `notes/openproposal_preexpert_seedrep_staticp99.md` 信息完整（inputs hash / run paths / eval convention / deltas / verdict）。

## 3) 风险与建议（面向下一步）

1) **该配置的“不稳定”是实证结论，不是审计缺口**  
   seed44 的失败幅度很小（`Δlpips_fg=+2.48e-4`），但在“必须同时 psnr_fg↑ & lpips_fg↓”的 gate 下仍应判 FAIL。

2) **若仍想在“不请专家”前再做一次最省事试探**（可选）  
   推荐只做 2 个 treatment run（复用已跑 baseline）：微调 `pseudo_mask_weight`（例如 `0.7`）以尝试压掉 lpips_fg 的边际退化，并仍保留 psnr_fg 提升；若两 seed 仍无法同时通过，则应止损并转入专家诊断或更换假设。

## 4) 审查 Gate Verdict

- 执行与审计：PASS
- 核心效果目标（两 seed 稳定通过）：FAIL

