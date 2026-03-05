# OpenProposal — Pre‑Expert Weight Tune 审查报告（weak `staticp99`, `w=0.7`）

Date: 2026-03-05 (UTC)  
Scope: 审查计划 `docs/plans/2026-03-05-openproposal-preexpert-weight-tune-staticp99.md` 的执行质量、可复核性与结论（THUman4.0 s00，local-only eval）。

## 0) 审查结论（摘要）

- **执行闭环：PASS**。Task 0–6 已完成；两条新 treatment（seed43/44，`w=0.7`）均完成 600-step 训练与 masked eval 落盘；same-init gate 与伪掩码路径/sha256 锁定成立。
- **科学结论：FAIL（不稳定）**。按严格 FG gate `psnr_fg↑ & lpips_fg↓`（并满足 `ΔtLPIPS<=+0.01`），两 seed 中仅 1 个通过：`OVERALL_OK=False`。
- **定位意义：增强“seed-sensitive”结论**。结合上一轮 `w=0.8` 的 2-seed 复核（同样 `OVERALL_OK=False`），可认为“简单调 `pseudo_mask_weight`”不足以把该配置稳定化；继续做 weight 扫描性价比很低。

## 1) 复核依据（产物与口径）

计划：
- `docs/plans/2026-03-05-openproposal-preexpert-weight-tune-staticp99.md`

审计 note（唯一事实源）：
- `notes/openproposal_preexpert_weight_tune_staticp99.md`

锁定输入（note 中已记录 sha256）：
- Plan‑B init：`outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- weak mask：`outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`

评测口径：
- `scripts/eval_masked_metrics.py --mask_source dataset --bbox_margin_px 32 --mask_thr 0.5 --lpips_backend auto`
- guardrail：`ΔtLPIPS <= +0.01`

## 2) Task-by-Task 完成度审查

### Task 0（Gate checks）：PASS

- `pytest -q` 通过（见执行汇报与 note）。

### Task 1（run matrix / baseline 复用）：PASS

- baseline 不重跑，复用：
  - `_seedrep_planb_init_600_seed43`
  - `_seedrep_planb_init_600_seed44`

### Task 2–3（两条 treatment 训练）：PASS

新增（append-only）：
- `_seedrep_weak_staticp99_w0.7_600_seed43`
- `_seedrep_weak_staticp99_w0.7_600_seed44`

复核点：
- 两条 treatment 的 `cfg.yml` 均满足：
  - `pseudo_mask_weight=0.7`
  - `pseudo_mask_end_step=600`
  - `init_npz_path` 与同 seed baseline 完全一致（same-init fairness）

### Task 4（masked eval）：PASS

- 两条 treatment 均产出 `stats_masked/test_step0599.json`。

### Task 5（2-seed decision gate）：PASS（结论为不稳定）

逐 seed 结论（引用 `notes/openproposal_preexpert_weight_tune_staticp99.md`）：
- seed43：`Δpsnr_fg=+0.245204`、`Δlpips_fg=-0.007882`、`ΔtLPIPS=+0.000599` → OK
- seed44：`Δpsnr_fg=+0.272591`、`Δlpips_fg=+0.001311`、`ΔtLPIPS=+0.000934` → FG fails

最终：
- `OVERALL_OK=False`

### Task 6（审计记录）：PASS

- `notes/openproposal_preexpert_weight_tune_staticp99.md` 信息完整（worktree、code hash、inputs sha、A/B 路径、口径、绝对值与 deltas、verdict）。

## 3) 审查 Gate Verdict

- 执行与审计：PASS
- 核心效果目标（两 seed 稳定通过）：FAIL

