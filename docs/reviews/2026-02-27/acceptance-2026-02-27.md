# 2026-02-27 Protocol v2 验收记录（Owner A / Owner B）

日期：2026-02-27  
验收目的：核对 protocol_v2（双阶段框架：Plan‑B + VGGT）阶段二产物是否“可复现 + 可审计 + 可答辩”，并明确未闭环项。

依据：
- 02-27 拍板：`docs/decisions/2026-02-27-dual-stage-academic-completeness.md`
- 路线图：`docs/plans/2026-02-27-postreview-roadmap.md`
- A 执行计划：`docs/plans/2026-02-27-owner-a-protocol-v2-gpu-plan.md`
- B 执行计划：`docs/plans/2026-02-27-owner-b-protocol-v2-nogpu-plan.md`

---

## 1) Owner A（GPU0）验收

### 1.1 产物核对（路径存在 + 可读）

✅ 动静解耦导出（tau_final=0.075436）：
- static-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- dynamic-only：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`

✅ tau 选择依据（p50/p90 + A/B + failure case）：
- `notes/velocity_stats_planb_init_600.md`
- `notes/protocol_v2_static_dynamic_tau.md`

✅ VGGT cache（token_proj，60 帧 × 8 cams，含 gate_framediff）：
- `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
- `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`

✅ Plan‑B + feature metric（smoke200 + full600 单次 gate + 止损）：
- smoke200 (lambda=0.005)：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/stats/test_step0199.json`
- full600 (lambda=0.005)：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/stats/test_step0599.json`
- 审计记录（含命令、对照与止损判定）：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`

### 1.2 结论核对（是否按协议止损）

✅ smoke200：训练稳定，无 NaN/爆炸；相对 `planb_init_smoke200` 基本持平；明显优于 baseline。  
✅ full600：相对 `planb_init_600` 的 test 指标出现 **PSNR↓ / LPIPS↑ / tLPIPS↑**，命中预设止损线并停止继续迭代（符合决议“不要盲调参烧卡”纪律）。

**验收结论（Owner A）：PASS。**

---

## 2) Owner B（No-GPU）验收

### 2.1 文档侧产物核对（对外版开题 + report-pack）

✅ 开题对外版（v2，双阶段叙事 + 贡献列表 + 端到端软先验口径 + 可实现定义 + SelfCap+tLPIPS + 资源/止损；并已回填 v2 产物路径）：
- `4D-Reconstruction-v2.md`

✅ protocol_v2 report-pack（路径索引 + 生成命令 + scoreboard 落盘）：
- `docs/report_pack/2026-02-27-v2/README.md`
- smoke200 scoreboard：`docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- full600 scoreboard：`docs/report_pack/2026-02-27-v2/scoreboard.md`

### 2.2 可复现性核对（命令可跑）

✅ 单测：`pytest -q scripts/tests` → 15 passed  
✅ 报表：`python3 scripts/build_report_pack.py` 可更新 `outputs/report_pack/metrics.csv`  
✅ 榜单：`python3 scripts/summarize_scoreboard.py ... --select_prefix outputs/protocol_v2/ --step 199|599` 可生成 v2 scoreboard（已落盘见上）

**验收结论（Owner B）：PASS。**

---

## 3) Owner A（GPU0）Follow-up 验收（protocol_v2，2026-02-27）

验收目的：核对 follow-up 是否补齐“VGGT 可解释材料 + 最小对应可视化”，并确认 stage‑2 趋势尝试遵守 gate/止损纪律。

### 3.1 VGGT 可解释材料（可答辩）

✅ cue/伪掩码证据包（可直接引用）：
- note：`notes/protocol_v2_vggt_cue_viz.md`
- `quality.json`：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
- viz：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/`（含 `grid_frame000000.jpg` 与各 cam overlay）

✅ token_proj feature 本体图（PCA->RGB）：
- note：`notes/protocol_v2_vggt_feature_pca.md`
- viz：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/viz_pca/`
- 工具：`scripts/viz_vggt_cache_pca.py` + 最小契约脚本 `scripts/tests/test_vggt_cache_pca_viz_contract.py`

### 3.2 stage‑2 趋势尝试（timebox + gate）

✅ framediff gating smoke200（两点试探，均未通过 gate，因此不跑 full600）：
- lam=0.005：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.005_warm100/stats/test_step0199.json`
- lam=0.002：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.002_warm100/stats/test_step0199.json`
- 审计追加：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`（含命令、delta、失败分析与“未过 gate 不跑 full600”的决策）

### 3.3 稀疏对应/可视化（最小闭环）

✅ token_proj temporal top‑k 对应可视化：
- viz：`outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam02_frame000000_to_000001.jpg`
- 方法/边界：`notes/protocol_v2_sparse_corr_viz.md`

**验收结论（Owner A follow-up）：PASS。**

✅ 已补齐（非阻塞项关闭）：新增 `scripts/viz_tokenproj_temporal_topk.py`，并在 `notes/protocol_v2_sparse_corr_viz.md` 写入一键复现命令入口。

---

## 4) Owner B（No-GPU）Follow-up 验收（protocol_v2，2026-02-27）

验收目的：核对 follow-up 是否把阶段二（protocol_v2）的“入口索引 / 可解释 scoreboard / 离线证据包 / Q&A”补齐到可答辩与可审计。

### 4.1 统一入口（单一入口索引）

✅ 主入口索引已补齐：
- `README.md`（protocol_v2 提交入口指向 `4D-Reconstruction-v2.md` 与 `docs/report_pack/2026-02-27-v2/README.md`）
- `docs/README.md`（索引项 0 指向同一入口）

### 4.2 可解释 scoreboard（含跨协议对比 Δ）

✅ v2 内部：
- smoke200：`docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- full600：`docs/report_pack/2026-02-27-v2/scoreboard.md`

✅ 跨协议对比（full600，含 baseline Δ 与风险提示）：
- `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

✅ 生成脚本与可复现性（含测试）：
- `scripts/summarize_scoreboard.py`
- `scripts/tests/test_summarize_scoreboard_protocol_v2.py`

### 4.3 evidence tarball 升级（stage‑2 真源纳入 + sha256 manifest）

✅ 打包逻辑升级（纳入 vggt_cache / cue_mining 轻量证据 / cfg.yml；默认不打包 pseudo_masks.npz）：
- `scripts/pack_evidence.py`
- `scripts/tests/test_pack_evidence_protocol_v2_sources.py`

✅ tarball 与 manifest 落盘：
- tarball：`outputs/report_pack_2026-02-27.tar.gz`
- manifest 快照：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- 说明：`docs/report_pack/2026-02-27-v2/README.md`

### 4.4 回填 A 产物与答辩 Q&A

✅ A 侧核心产物路径回填（动静解耦 / VGGT cache / stats / 审计 / scoreboard）：
- `docs/report_pack/2026-02-27-v2/README.md`
- `4D-Reconstruction-v2.md`

✅ 答辩必问点（短答案 + 证据指针）：
- `notes/qna.md`

**验收结论（Owner B follow-up）：PASS。**

---

## 5) protocol_v2 next 增补验收（A/B 同日联动）

验收目的：把 A 新增 run（smoke gate 扩展 + 单次 full600 补跑）纳入同一证据链，并由 B 完成 scoreboard/tarball/narrative 同步。

### 5.1 Owner A 新增 run（Intake + gate）

✅ 新增 run 最小可审计产物齐全（训练类目录均有 `cfg.yml` + `stats/test_step0199|0599.json`）：
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16/`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100/`
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/`

✅ gate/止损判定（以 `notes/protocol_v2_planb_feat_smoke200_owner_a.md` 与 scoreboard 为准）：
- smoke200：`start150_ramp50_every16` 通过 gate；`patchk4_hw3` 与 `framediff` 两点均未通过。
- full600：`start300_ramp200_every16` 相对 `planb_init_600` 为 **PSNR↑ / LPIPS↑ / tLPIPS↑**，未触发“全线劣化”硬止损，但未形成全指标增益。

### 5.2 Owner B 同步落盘（No‑GPU）

✅ 报表与榜单同步：
- `python3 scripts/build_report_pack.py` 已刷新 `outputs/report_pack/metrics.csv`
- `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- `docs/report_pack/2026-02-27-v2/scoreboard.md`
- `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

✅ 离线包与叙事同步：
- `python3 scripts/pack_evidence.py` 已重打 `outputs/report_pack_2026-02-27.tar.gz`
- `docs/report_pack/2026-02-27-v2/manifest_sha256.csv` 已从 tar 内解包回填
- `docs/report_pack/2026-02-27-v2/README.md`、`4D-Reconstruction-v2.md`、`notes/qna.md` 已更新到最新 gate 口径

**增补结论（A/B）：PASS。**

---

## 6) protocol_v2 stage‑2 trade-off 增补验收（Owner B / No‑GPU）

验收目的：把 A 新增的 trade-off 诊断证据（定量 + 定性）纳入同一证据链，并完成同日离线包回填。

### 6.1 Intake 与最小可审计检查

✅ 训练类新增 run 保持可审计（`cfg.yml` + `stats/test_step0199|0599.json` + 视频）：
- `planb_feat_v2_smoke200_lam0_sanity`
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16`
- `planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16`
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf`
- `planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100`
- `planb_feat_v2_full600_lam0.005_start300_ramp200_every16`

✅ 导出类补齐（2026-02-28）：
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.075432/videos/traj_4d_step599.mp4`

### 6.2 trade-off 证据落盘

✅ 定量（已刷新）：
- `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- `docs/report_pack/2026-02-27-v2/scoreboard.md`
- `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

✅ 定性（side-by-side，step599）：
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/baseline_vs_planbfeat_full600_step599.mp4`

### 6.3 结论（口径收口）

- stage‑2 当前为 mixed trend：`PSNR` 有单点改善，但 `LPIPS/tLPIPS` 未同步改善。
- 继续遵守预算纪律：不新增 full600 sweep，转向机理分析与可解释证据补齐。

**增补结论（Owner B / trade-off）：PASS。**

---

## 7) protocol_v2 C2(noconf) full600 集成增补验收（Owner B / No‑GPU，2026-02-28）

验收目的：核对“新增 1 次 C2(noconf) full600 预算闸门”结果，并将结论同步到同一证据链。

### 7.1 Intake 结果

- 目标目录未发现：`outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16_noconf/`
- 结论：本轮预算未批准（或未执行），因此无新增 `..._noconf full600` 训练产物可纳入。

### 7.2 No‑GPU 同步动作

- 已刷新：
  - `outputs/report_pack/metrics.csv`
  - `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
  - `docs/report_pack/2026-02-27-v2/scoreboard.md`
  - `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`
- 已重打并回填：
  - `outputs/report_pack_2026-02-28.tar.gz`
  - `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- 口径已同步：
  - `docs/report_pack/2026-02-27-v2/README.md`
  - `4D-Reconstruction-v2.md`
  - `notes/qna.md`

### 7.3 验收结论

- 按预算纪律收口：不新增 C2(noconf) full600，采用 smoke 趋势 + full600 trade-off 定性证据完成阶段二收口。

**增补结论（Owner B / C2 full600 integration）：PASS。**

---

## 8) dual‑GPU smoke sweep 增补验收（Owner A/B，2026-02-28）

验收目的：确认 dual‑GPU smoke sweep（A 侧 framediff 口径 + B 侧 seed 噪声带）已完成 intake、指标收口、离线包纳管，并保持预算纪律不漂移。

### 8.1 Intake（run tag 清单）

✅ A 侧（framediff p=0.02）：
- `planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16`
- `planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start200_ramp50_every16`
- `planb_feat_v2_smoke200_framediff_p0.02_lam0.002_start200_ramp50_every16`

✅ B 侧（GPU1 seed sweep + 小网格）：
- `planb_feat_v2_smoke200_lam0_sanity_s42_gpu1`
- `planb_feat_v2_smoke200_lam0_sanity_s43_gpu1`
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s42_gpu1`
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s43_gpu1`
- `planb_feat_v2_smoke200_lam0.005_start200_ramp50_every16_s42_gpu1`
- `planb_feat_v2_smoke200_lam0.002_start200_ramp50_every16_s42_gpu1`

✅ A 侧（GPU0，noconf 候选 seed 复现，用于稳定性判定）：
- `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0`

### 8.2 指标收口引用

✅ 统一以以下文档为准：
- `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- `docs/report_pack/2026-02-27-v2/README.md`（`2.6) 2026-02-28 dual-GPU smoke sweep` 小节）

### 8.3 离线证据包与 manifest

✅ 当天离线包与校验清单：
- `outputs/report_pack_2026-02-28.tar.gz`
- `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

### 8.4 结论

- dual‑GPU smoke sweep 验收：**PASS**。
- 当前未触发“新增 full600 预算讨论”条件；继续执行 mixed trend + failure analysis 收口。

---

## 9) Owner A GPU0 Follow-up（export-only + gate diagnostics，2026-02-28）

验收目的：确认 A 侧按计划补齐“可编辑性演示（动静分层导出）+ framediff gate 诊断产物”，并确保产物路径可纳入离线包审计。

✅ 导出视频（step599）：
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.075436/videos/traj_4d_step599.mp4`

✅ framediff gate 诊断（report-pack 诊断目录，适配离线包打包）：
- `outputs/report_pack/diagnostics/gate_framediff_p010/`
- `outputs/report_pack/diagnostics/gate_framediff_p002/`

✅ 收口结论（seed44 与噪声带口径）：见 `notes/protocol_v2_planb_feat_smoke200_owner_a.md`。

**验收结论（Owner A GPU0 follow-up）：PASS。**

---

## 10) temporal diagnostics 增补验收（Owner A/B，2026-02-28）

验收目的：确认 stage‑2 的 temporal diagnostics（A: 像素域 temporal diff，B: 感知域 tLPIPS curve）已纳入同一证据链并进入离线包审计。

### 10.1 Intake（新增诊断产物）

✅ A 侧（像素域 temporal diff）：
- `outputs/report_pack/diagnostics/temporal_diff_planb_init_600_test_step599.csv`
- `outputs/report_pack/diagnostics/temporal_diff_planb_feat_v2_full600_test_step599.csv`
- `outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv`
- `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`

✅ B 侧（感知域 tLPIPS curve）：
- `outputs/report_pack/diagnostics/tlpips_curve_planb_init_600_test_step599.csv`
- `outputs/report_pack/diagnostics/tlpips_curve_planb_feat_v2_full600_test_step599.csv`
- `outputs/report_pack/diagnostics/tlpips_curve_delta_planbfeat_minus_planb_test_step599.csv`
- `outputs/report_pack/diagnostics/tlpips_curve_topk_planbfeat_minus_planb_test_step599.md`
- `notes/protocol_v2_tlpips_curve_diagnostics.md`

### 10.2 Evidence（离线包）

✅ 统一证据包与清单：
- `outputs/report_pack_2026-02-28.tar.gz`
- `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

### 10.3 结论

- temporal diagnostics 增补验收：**PASS**。
- 当前结论仍为 mixed trend，不触发新增 full600 预算讨论。
