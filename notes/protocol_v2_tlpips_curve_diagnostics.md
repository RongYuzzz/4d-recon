# protocol_v2 tLPIPS curve diagnostics（Owner B）

## 诊断产物

- `outputs/report_pack/diagnostics/tlpips_curve_planb_init_600_test_step599.csv`
- `outputs/report_pack/diagnostics/tlpips_curve_planb_feat_v2_full600_test_step599.csv`
- `outputs/report_pack/diagnostics/tlpips_curve_delta_planbfeat_minus_planb_test_step599.csv`
- `outputs/report_pack/diagnostics/tlpips_curve_topk_planbfeat_minus_planb_test_step599.md`

## 一句话结论

- `planbfeat - planb` 的 tLPIPS top-k 峰值集中在 `frame_prev=41 -> frame_cur=42` 及其邻近帧段（38-39、44-45、54-56），与 `notes/protocol_v2_stage2_tradeoff_qual.md` 中的失败锚点（41-42 为首）整体一致。
