# Owner B（No‑GPU）后续计划（protocol_v2 follow-up）

日期：2026-02-27  
目标：在不使用 GPU 的前提下，把 protocol_v2（阶段二）从“已跑通”推进到“可答辩/可审计/可打包交付”，并把后续 A 的新增产物以**填空式**方式纳入同一证据链。

依据：
- 路线图：`docs/plans/2026-02-27-postreview-roadmap.md`
- 决议：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- 验收记录：`docs/reviews/2026-02-27/acceptance-2026-02-27.md`

约束：
- 不使用 GPU（所有任务必须可在 CPU/本地环境完成）
- `v26 + protocol_v1` 证据链不动；所有阶段二新增内容统一归入 `protocol_v2`

---

## Task 1（必须）：把“对外叙事”与“证据链”固化成单一入口

### 1.1 统一文档入口（避免答辩时找不到版本）

- 以 `4D-Reconstruction-v2.md` 作为对外可提交版（阶段一 + 阶段二口径统一，且引用真实产物路径）。
- 在 `README.md` 与 `docs/README.md` 增加明确索引：
  - “开题对外版：`4D-Reconstruction-v2.md`”
  - “阶段二证据包：`docs/report_pack/2026-02-27-v2/README.md`”
- 明确标注 `4D-Reconstruction.md` 的定位（历史原稿/不再作为提交版），防止“口径打架”。

**验收标准**：新人只打开 `README.md` 即可定位 v2 开题 + v2 report-pack。

---

## Task 2（必须）：把 v2 scoreboard 做成“能解释”的对比表

> 当前 v2 scoreboard 仅筛 `outputs/protocol_v2/`，Δ 列为空（缺 baseline 行）；答辩时很难一句话解释“相对阶段一/基线发生了什么”。

### 2.1 生成“跨协议对比”的 full600 scoreboard（CPU）

- 生成一个包含 `baseline_600 / planb_init_600 / planb_feat_v2_full600_*` 的对比表（同 dataset、同 step=599）：
  - 输出建议：`docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
  - 生成方式：`scripts/summarize_scoreboard.py` 保持 `--select_contains selfcap_bar_8cam60f` 与 `--step 599`，但**不要只筛 protocol_v2 前缀**（保证 baseline 行进入 selected，从而 Δ 列可计算）。

### 2.2 更新 report-pack README 的“推荐读法”

- 在 `docs/report_pack/2026-02-27-v2/README.md` 增加两条阅读建议：
  1) 先看 `scoreboard_full600_vs_v1.md`（定位 stage‑2 相对 stage‑1 是否增益/止损）  
  2) 再看 `scoreboard.md / scoreboard_smoke200.md`（只看 v2 内部对照）

**验收标准**：表格里至少能看到 `baseline_600` 的 Δ 列，以及 `planb_init_600` 与 `planb_feat_v2_full600_*` 的相对趋势（哪怕是负增益也要可解释）。

---

## Task 3（必须）：升级 evidence tarball，把 protocol_v2 的“关键真源”打进去

> 现在 `scripts/pack_evidence.py` 会打包 stats/video，但 **不包含** `outputs/vggt_cache/*/gt_cache.npz`、也不包含每次 run 的 `cfg.yml`，会导致“可复现/可审计”在 stage‑2 上被质疑。

### 3.1 扩展 `scripts/pack_evidence.py` 的收集范围（No‑GPU 修改即可）

建议新增纳入：
- `outputs/vggt_cache/**/{gt_cache.npz,meta.json}`
- `outputs/cue_mining/**/{quality.json,viz/*}`（只收可视化与质量统计，避免把所有 npz 都塞进去）
- `outputs/**/cfg.yml`（训练/导出配置真源）

### 3.2 生成新的 evidence tarball 并记录 sha256 manifest

- 运行 `python3 scripts/pack_evidence.py` 产出新包（默认落 `outputs/report_pack_<YYYY-MM-DD>.tar.gz`）
- 在 `docs/report_pack/2026-02-27-v2/README.md` 记录：
  - tarball 路径
  - `manifest_sha256.csv` 用法（如何核对）

**验收标准**：离线给别人一份 tarball，对方能看到 stage‑2 的 cache 真源、配置真源、scoreboard 与核心可视化证据。

---

## Task 4（并行对接 A）：把 A 的 follow-up 产物“填空式回填”

触发条件：A 交付任一新增产物（VGGT PCA 图 / 新的 smoke/full run / 稀疏对应可视化）。

B 的动作（不需要 GPU）：
- 更新 `docs/report_pack/2026-02-27-v2/README.md` 与 `4D-Reconstruction-v2.md` 引用路径
- `python3 scripts/build_report_pack.py` 刷新 `outputs/report_pack/metrics.csv`
- 重跑 scoreboard（step=199/599），并在 README 中注明“新增 run 的止损/结论”

**验收标准**：所有新增产物都能在 report-pack README 中 1 次点击定位到路径；scoreboard 与文字结论同步更新。

---

## Task 5（可选但强建议）：答辩 Q&A 固化（No‑GPU）

在 `notes/qna.md` 增补 5 个必问点的“短答案 + 证据指针”：
- baseline 是什么（本仓库 baseline_600 的含义与路径）
- 为什么 stage‑2 目前止损（full600 vs planb_init_600 的三项对比与审计 note）
- “端到端”如何定义（soft prior vs 2D 强监督前置）
- 为什么用 SelfCap+tLPIPS（与开题中 mIoU/多数据集承诺的取舍）
- 动静解耦 demo 的意义（τ 选择依据与失败例在哪里）

