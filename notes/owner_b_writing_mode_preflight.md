# Owner B Writing Mode Preflight

- Date: 2026-02-26 04:22:25 UTC
- Worktree: /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode
- HEAD: 5325327698b7ead4fc99bae490748f9aa1b79f39
- Branch: detached (origin/main)

## Recent Commits
```
5325327 docs(plan): add owner-b no-gpu writing+diagnostics plan (2026-02-26)
e6dd4a9 docs(plan): add owner-a planb 48h gate + seg2 control plan (2026-02-26)
7400a88 docs: record plan-b pivot decision and execution (2026-02-26)
63b1c9e feat(planb): add velocity init script + runner
2730318 docs(review): add 2026-02-26 meeting pack
```

## Baseline Tests
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
Ran 1 test in 0.409s

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
