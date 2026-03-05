# OpenProposal — Phase 6 审查报告（FG Realign Follow-up）

Date: 2026-03-05 (UTC)  
Scope: 审查计划 `docs/plans/2026-03-05-openproposal-fg-realign-followup.md` 的**完成情况、可复核性与偏差**（Phase 3/4 follow-up）。

## 0) 审查结论（摘要）

- **总体结论：PASS（按计划完整交付）**。Task 0–6 全部完成；新增/修改的脚本均有对应 `pytest` contract test；本分支全量测试通过。
- **Phase 3 follow-up 达成计划目标的关键部分**：通过 pseudo-mask scaling 消除了“mask 近似常数/弱监督 no-op”的明确风险，并用 direction flip（static_from_dynamic_scaled vs dynamic_scaled）给出可解释的 A/B 结果与下一步方向建议。
- **Phase 4 follow-up 达成“有效性澄清”目标**：`gating=none` 与 `phi_size` 提升（ds4→ds2）都能稳定激活监督路径（`vggt_feat/active` 与 token grid 数量一致），但前景指标未稳定优于 baseline，因此止损结论成立。
- **证据链合规**：仅提交 `scripts/`、`docs/`、`notes/` 与 `scripts/tests/`；未提交 `data/`、`outputs/`（local-eval only）。

关联分支 / PR（用于代码审阅）：
- Branch: `owner-b-20260305-fg-realign`
- PR: `https://github.com/RongYuzzz/4d-recon/pull/3`

## 1) 审查依据（分支、提交、测试）

本次计划相关提交（按时间顺序）：
- `8285d58` `docs(notes): add Phase6 fg realign local-only scope note`
- `8656e08` `feat(cue): add pseudo mask scaling tool`
- `bab659c` `feat(metrics): add psnr_fg_area and lpips_fg_comp to masked evaluator`
- `a0f8527` `feat(diagnostics): add pseudomask healthcheck sweep tool`
- `de45e08` `docs(notes): Phase6 Phase3 fg realign follow-up results`
- `51051fb` `docs(notes): Phase6 Phase4 fg realign follow-up results`
- `d2997f8` `docs(review): append Phase6 fg realign follow-up outcomes`
- `d71559a` `docs(plans): add Phase6 fg realign follow-up plan`

测试复核：
- `pytest -q`：**32 passed**（本次审查已在 worktree 中复跑通过）。

## 2) Task-by-Task 完成度审查（含证据点）

### Task 0 — Worktree + Gate Checks（PASS）

计划要求：
- 单独 worktree + 测试干净通过；
- VGGT 离线预检；
- 锁定 baseline `init_npz_path`（公平性 gate）并记录 sha256；
- 记录 local-only 纪律说明。

复核证据：
- 纪律 note：`notes/openproposal_phase6_fg_realign_scope.md`
- baseline init 锁定（同一文件用于所有 follow-up treatments）：
  - `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
  - sha256：`d6ce23a2a2116ce72dddee9a8b4e64741cdfe5f4ee91bae79cea3b695ca4c88f`
- VGGT cache dir 存在：`/root/.cache/huggingface/hub/models--facebook--VGGT-1B`

### Task 1 — Pseudo-Mask Scaling Tool（PASS）

计划要求：TDD 新增 scaling 工具，能把 uint8/float pseudo mask 标定到 float32 [0,1]，并产出可审计的 scale 元数据。

复核证据：
- 脚本：`scripts/scale_pseudo_masks_npz.py`
- 合同测试：`scripts/tests/test_scale_pseudo_masks_npz_contract.py`
- 实际 Phase 3 follow-up 使用产物（均存在）：
  - `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_dyn_p99.npz`
  - `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`

### Task 2 — Extend Foreground Evaluator（PASS）

计划要求：在 `scripts/eval_masked_metrics.py` 增加更敏感的前景口径，并在契约测试中锁定输出字段。

复核证据：
- 修改脚本：`scripts/eval_masked_metrics.py`
  - 新增字段：`psnr_fg_area`、`lpips_fg_comp`、`lpips_backend`
- 修改契约测试：`scripts/tests/test_eval_masked_metrics_contract.py`
- 实际落盘 JSON（抽样验证 key 存在）：
  - `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit_r1/stats_masked/test_step0599.json`

### Task 3 — Mask Health-Check Sweep Tool（PASS）

计划要求：提供 thr_pred sweep + top-p overlap 的最小体检工具，避免 Phase 2/3 被阈值口径误导。

复核证据：
- 脚本：`scripts/mask_healthcheck_sweep.py`
- 合同测试：`scripts/tests/test_mask_healthcheck_sweep_contract.py`

### Task 4 — Phase 3 Follow-up Runs（PASS）

计划要求：
- 产出 dynamic_scaled 与 static_from_dynamic_scaled 两条 weak-fusion treatment（same-init）；
- masked eval（真实 LPIPS）；
- TB 标量导出证明 weak path 非 no-op；
- 结论写入 note 并提交。

复核证据：
- 结果 note：`notes/openproposal_phase6_fg_realign_phase3.md`
- same-init 公平性 gate（cfg.yml 复核一致）：
  - baseline：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`
  - treat A：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_dynp99_w0.8_600_r1`
  - treat B：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_600_r1`
  - 三者 `init_npz_path` 均为同一文件：`outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- masked eval 落盘（均存在）：
  - `.../stats_masked/test_step0599.json`
- weak path activity（TB 导出 CSV 存在）：
  - `outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_init_weak_dynp99_w0.8_600_r1_tb_scalars.csv`
  - `pseudo_mask/active_ratio` 在约 `0.01~0.03`（远离 1.0 饱和）

偏差 / 风险提示（不影响结论但需声明）：
- 存在一个未完成的目录 `planb_init_weak_dynp99_w0.8_600`（缺 `stats/test_step0599.json`），应视为 **aborted/无效**；本次结论以 `_r1` 目录为准。

### Task 5 — Phase 4 Follow-up Runs（PASS）

计划要求：
- feature-loss follow-up 先去 gating（`VGGT_FEAT_GATING=none`）；
- 若仍失败，再用 ds2 提升 `phi_size`；
- 必须证明监督路径激活（`vggt_feat/active` 与 `phi_size` 匹配）；
- masked eval 落盘 + note 记录。

复核证据：
- 结果 note：`notes/openproposal_phase6_fg_realign_phase4.md`
- 两条 treatment（same-init）：
  - ds4 nogate：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_nogate_lam0.005_600_sameinit_r1`
  - ds2 nogate：`outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1`
- cache meta（均存在）：
  - ds4：`outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10/meta.json`（`phi_size=[8,9]`）
  - ds2：`outputs/vggt_cache/openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds2_nogate/meta.json`（`phi_size=[16,18]`）
- TB 导出 CSV（均存在，且 `vggt_feat/active` 匹配 token grid）：
  - `outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_feat_v2_nogate_lam0.005_600_sameinit_r1_tb_scalars.csv`（`72`）
  - `outputs/qualitative_local/openproposal_phase6/tb_scalars/planb_feat_v2_ds2_nogate_lam0.005_600_sameinit_r1_tb_scalars.csv`（`288`）
- masked eval 落盘（均存在）：
  - `.../stats_masked/test_step0599.json`

### Task 6 — Update Diagnosis Docs（PASS）

计划要求：将 follow-up 结果写回专家诊断材料/失败分析材料，形成“更新后的 failure boundary”。

复核证据：
- `docs/reviews/2026-03-05/expert-diagnosis-pack_phase3-4.md`（包含 “Follow-up outcome (Phase 6)”）
- `docs/reviews/2026-03-05/openproposal-phase3-4-failure-analysis.md`（包含同名小节）

## 3) 本计划的关键产出（面向后续迭代）

代码与工具层面（可复用、可审计）：
- pseudo mask scaling：`scripts/scale_pseudo_masks_npz.py`
- mask healthcheck sweep：`scripts/mask_healthcheck_sweep.py`
- fg evaluator 更敏感口径：`scripts/eval_masked_metrics.py`（`psnr_fg_area/lpips_fg_comp`）

实验结论层面（用于下一步决策）：
- Phase 3：weak-fusion 已确认不再是 no-op；direction flip 结果显示 `static_from_dynamic_scaled` 在 fg-local 指标上更占优（但存在 full-frame 代价）。
- Phase 4：监督路径已确认被激活（非“loss 没算”），但当前 `token_proj + cosine + lambda=0.005` 在该 scene 上仍不稳定赢 fg，止损合理。

