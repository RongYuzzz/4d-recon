# Owner B PlanB Writing Preflight

- Date: 2026-02-26 05:06:11 UTC
- Worktree: /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode
- Branch: owner-b-20260226-writing-mode
- HEAD: 712ccbe5aa4726b2e24f15043f125bea4d74e409

## Task B51 Required Output Checks
- READY: /root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600
- READY: /root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600
- READY: /root/autodl-tmp/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json
- READY: /root/autodl-tmp/projects/4d-recon/outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600

## Recent Commits
```
712ccbe docs(notes): add owner-b writing mode preflight record
d5a2478 docs(report-pack): snapshot planb verdict and seg2 defense (2026-02-26-v16)
b5d321d feat(diagnostics): export tensorboard scalars for feature-loss failure attribution
cf7cad6 fix(scoreboard): include planb runs and avoid false risk hints on missing cores
5325327 docs(plan): add owner-b no-gpu writing+diagnostics plan (2026-02-26)
```

## Baseline tests (scripts/tests/test_*.py)
```
[RUN] scripts/tests/test_adapt_hf_sample.py
PASS: adapt_hf_sample_to_freetime filters sparse model and builds frame folders
[PASS] scripts/tests/test_adapt_hf_sample.py
[RUN] scripts/tests/test_adapt_hf_sample_per_frame_sparse.py
PASS: adapt_hf_sample_to_freetime exports per_frame_sparse triangulation
[PASS] scripts/tests/test_adapt_hf_sample_per_frame_sparse.py
[RUN] scripts/tests/test_analyze_smoke200_m1.py
PASS: analyze_smoke200_m1 outputs table + pareto + recommendation
[PASS] scripts/tests/test_analyze_smoke200_m1.py
[RUN] scripts/tests/test_build_report_pack.py
PASS: build_report_pack supports args + derived columns
[PASS] scripts/tests/test_build_report_pack.py
[RUN] scripts/tests/test_cue_mining_contract.py
PASS: cue_mining contract npz+viz outputs are valid
[PASS] scripts/tests/test_cue_mining_contract.py
[RUN] scripts/tests/test_cue_mining_quality_stats.py
PASS: cue_mining quality stats contract is valid
[PASS] scripts/tests/test_cue_mining_quality_stats.py
[RUN] scripts/tests/test_export_tb_scalars.py
PASS: export_tb_scalars exports selected tags and warns on missing tags
[PASS] scripts/tests/test_export_tb_scalars.py
[RUN] scripts/tests/test_export_triangulation_adapter.py
PASS: export_triangulation adapter tests
[PASS] scripts/tests/test_export_triangulation_adapter.py
[RUN] scripts/tests/test_export_velocity_stats.py
PASS: export_velocity_stats emits required markdown fields
[PASS] scripts/tests/test_export_velocity_stats.py
[RUN] scripts/tests/test_feature_loss_v2_artifacts_exist.py
PASS: v2 artifacts exist
[PASS] scripts/tests/test_feature_loss_v2_artifacts_exist.py
[RUN] scripts/tests/test_init_velocity_from_points_contract.py
PASS: planb init_velocity_from_points emits expected artifacts/schema
[PASS] scripts/tests/test_init_velocity_from_points_contract.py
[RUN] scripts/tests/test_pack_evidence.py
PASS: pack_evidence excludes large dirs and writes manifest
[PASS] scripts/tests/test_pack_evidence.py
[RUN] scripts/tests/test_run_gate1_smoke_frame_count.py
PASS: run_gate1_smoke remaps train range to exported triangulation frame count
[PASS] scripts/tests/test_run_gate1_smoke_frame_count.py
[RUN] scripts/tests/test_run_mvp_repro_defaults.py
PASS: run_mvp_repro defaults include canonical SelfCap tar/output + adapter invocation
[PASS] scripts/tests/test_run_mvp_repro_defaults.py
[RUN] scripts/tests/test_run_pipeline_env_flags.py
PASS: run_pipeline supports render trajectory env flags
[PASS] scripts/tests/test_run_pipeline_env_flags.py
[RUN] scripts/tests/test_run_pipeline_extra_train_args.py
PASS: run_pipeline supports EXTRA_TRAIN_ARGS passthrough
[PASS] scripts/tests/test_run_pipeline_extra_train_args.py
[RUN] scripts/tests/test_selfcap_adapter.py
PASS: selfcap adapter tests
[PASS] scripts/tests/test_selfcap_adapter.py
[RUN] scripts/tests/test_selfcap_cli_no_images.py
.
----------------------------------------------------------------------
Ran 1 test in 0.112s

OK
[PASS] scripts/tests/test_selfcap_cli_no_images.py
[RUN] scripts/tests/test_selfcap_parsers.py
......
----------------------------------------------------------------------
Ran 6 tests in 0.002s

OK
[PASS] scripts/tests/test_selfcap_parsers.py
[RUN] scripts/tests/test_strong_fusion_flags.py
PASS: strong fusion flags and temporal correspondence loss hooks exist in trainer
[PASS] scripts/tests/test_strong_fusion_flags.py
[RUN] scripts/tests/test_summarize_scoreboard.py
PASS: summarize_scoreboard supports filtering + strong variants + deltas
[PASS] scripts/tests/test_summarize_scoreboard.py
[RUN] scripts/tests/test_t0_config_flags.py
PASS: all required T0 config flags exist
[PASS] scripts/tests/test_t0_config_flags.py
[RUN] scripts/tests/test_temporal_correspondences_klt_contract.py
.
----------------------------------------------------------------------
Ran 1 test in 0.448s

OK
[PASS] scripts/tests/test_temporal_correspondences_klt_contract.py
[RUN] scripts/tests/test_token_proj_determinism.py
PASS: token-proj projection is deterministic by seed
[PASS] scripts/tests/test_token_proj_determinism.py
[RUN] scripts/tests/test_token_proj_resize_alignment.py
PASS: token_proj resize alignment is correct
[PASS] scripts/tests/test_token_proj_resize_alignment.py
[RUN] scripts/tests/test_vggt_cache_contract.py
PASS: VGGT cache contract outputs are valid
[PASS] scripts/tests/test_vggt_cache_contract.py
[RUN] scripts/tests/test_vggt_feat_v2_flag_tokens.py
PASS: VGGT feature-loss v2 tokens exist in trainer
[PASS] scripts/tests/test_vggt_feat_v2_flag_tokens.py
[RUN] scripts/tests/test_vggt_feature_loss_flags.py
PASS: VGGT feature-loss flags and hooks exist in trainer
[PASS] scripts/tests/test_vggt_feature_loss_flags.py
[RUN] scripts/tests/test_vggt_preprocess_consistency_dummy.py
PASS: vggt preprocess consistency dummy mode
[PASS] scripts/tests/test_vggt_preprocess_consistency_dummy.py
[RUN] scripts/tests/test_weak_fusion_flags.py
PASS: weak fusion flags and weighted L1 hooks exist in trainer
[PASS] scripts/tests/test_weak_fusion_flags.py
[RUN] scripts/tests/test_write_throughput_json.py
PASS: write_throughput_json emits canonical schema
[PASS] scripts/tests/test_write_throughput_json.py
```

All scripts/tests/test_*.py passed.
