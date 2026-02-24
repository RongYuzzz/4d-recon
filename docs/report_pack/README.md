# Report Pack Snapshots

这里存放的是“汇报用证据包”的**文本快照**（便于版本化与长期保存），主要来源于 `artifacts/report_packs/report_pack_YYYY-MM-DD.tar.gz` 里提取的：
- `metrics.csv`
- `ablation_notes.md`
- `failure_cases.md`
- （可选）`manifest_sha256.csv`

说明：
- 这些是当时的输出快照，可能与当前代码/参数略有差异，但用于追溯“当时汇报材料”。
- 如果要生成最新版本，优先用主线脚本：`scripts/build_report_pack.py` + `scripts/pack_evidence.py`。

