# protocol_v2 temporal diff top-k frame snapshots (Pred half)

诊断目标：把 `planb_init_600 -> planb_feat_v2_full600_*` 的时序不稳定用“帧对锚点 + 帧级快照”固化，便于离线审计与答辩复现。

证据产物：
- `outputs/report_pack/diagnostics/temporal_diff_curve_planb_vs_planbfeat_test_step599.png`
- `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`
- `outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv`
- `outputs/report_pack/diagnostics/temporal_diff_topk_frames_planbfeat_minus_planb_test_step599/README.md`

一句话结论：
- top-k 最大增量帧对集中在 `37-45` 区间，rank1 为 `(41,42)`；对应的帧级快照见 `temporal_diff_topk_frames_.../pair_0041_0042.jpg`。
