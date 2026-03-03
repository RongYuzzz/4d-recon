# protocol_v2 spatial metrics top-k frame snapshots

- 本目录用于审计 `planb_feat_v2_full600 - planb_init_600` 在 `test_step599` 上按 `delta_mae` 降序的 top-k 逐帧快照（每帧含 planb/planbfeat 的 GT、Pred、`|Pred-GT|`）。
- 快照索引见：`outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599/README.md`。
- 本次 top-k 基本集中在 `52-59`（另有 `frame_0000`），与 temporal / tLPIPS 的 `41->42` 锚点互补：前者解释末段空间误差局部劣化，后者解释跨帧一致性变化。
