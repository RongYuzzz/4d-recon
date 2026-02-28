# protocol_v2 report-pack（2026-02-27-v2）

## 1) 目标与不变量

- 本目录仅用于汇总 `protocol_v2` 的阶段二实验证据：几何语义先验（VGGT feature/pseudomask）与动静解耦演示。
- 所有新实验统一写入 `outputs/protocol_v2/...`，并与阶段一证据链隔离管理，避免口径混用。
- 结果解释遵循同一规则：先看可复现日志与产物路径，再看指标；不接受无路径、无配置、无日志的结论。

## 2) A 侧产物回填状态（2026-02-27）

1. ✅ static/dynamic 视频（已发现）
   - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
   - `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
   - τ 选择依据与失败例：`notes/velocity_stats_planb_init_600.md`、`notes/protocol_v2_static_dynamic_tau.md`
2. ✅ VGGT cache（已回填）
   - `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
   - `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`
3. ✅ Plan‑B + feature metric stats（已回填，含 gate/止损状态）
   - smoke200（基线）：
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_warm100/stats/test_step0199.json`（趋势持平）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.01_warm100/stats/test_step0199.json`（次优，未作为 full600 外推）
   - smoke200（next 补充）：
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0_sanity/stats/test_step0199.json`（可比性检查通过）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16/stats/test_step0199.json`（通过 smoke gate）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.002_start150_ramp50_every16/stats/test_step0199.json`（通过 gate；但 tLPIPS 退步扩大）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf/stats/test_step0199.json`（通过 gate；减轻 tLPIPS 退步）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_patchk4_hw3_warm100/stats/test_step0199.json`（未通过 smoke gate）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.005_warm100/stats/test_step0199.json`（未通过 smoke gate）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_framediff_p0.10_lam0.002_warm100/stats/test_step0199.json`（未通过 smoke gate）
   - full600：
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_warm100_ramp400/stats/test_step0599.json`（触发止损）
     - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/stats/test_step0599.json`（未触发硬止损；PSNR↑但 LPIPS/tLPIPS 退步）
   - 审计记录（命令/对照/gate 判定）：`notes/protocol_v2_planb_feat_smoke200_owner_a.md`
4. ✅ VGGT cue / 伪掩码证据包（可答辩）
   - note：`notes/protocol_v2_vggt_cue_viz.md`
   - quality：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json`
   - viz：`outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/`
5. ✅ token_proj feature PCA(3D)->RGB 可视化（可答辩）
   - note：`notes/protocol_v2_vggt_feature_pca.md`
   - viz：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/viz_pca/`
   - 工具：`scripts/viz_vggt_cache_pca.py`
6. ✅ 稀疏对应（token top‑k）可视化（timebox deliverable）
   - note：`notes/protocol_v2_sparse_corr_viz.md`
   - viz：`outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/`
   - 工具：`scripts/viz_tokenproj_temporal_topk.py`
7. ✅ Intake checklist（新增 RESULT_TAG）
   - 训练类目录均通过“最小可审计产物”检查：`cfg.yml` + `stats/test_step0199|0599.json` 齐全。
   - `export_planb_*` 属于导出视频目录（含 `videos/traj_4d_step*.mp4`），不纳入训练 gate 判定。
   - `export_planbfeat_*` 已补齐导出视频（τ 选择依据与失败边界：`notes/velocity_stats_planb_feat_v2_full600_start300.md`、`notes/protocol_v2_static_dynamic_tau_planb_feat_v2_full600.md`）。

结论摘要（以 scoreboard 与审计 note 为准）：
- smoke200：存在至少一个“非全线退步”候选（`start150_ramp50_every16`），其余候选多为 gate fail。
- full600：`warm100_ramp400` 触发止损；`start300_ramp200_every16` 为“PSNR 单点改善 + LPIPS/tLPIPS 退步”的混合趋势，未形成可宣称增益。
- 预算纪律：本轮 full600 已达上限（单次补跑后收口）；新增 `..._noconf full600` 预算未获批，停止新增 full600 sweep。

## 2.5) Stage‑2 trade-off diagnosis（2026-02-27 同日增补）

### side-by-side 定性对比（step599）

1. baseline vs planb（阶段一收益基线）  
   - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
2. planb vs planb+feat（阶段二代价观察）  
   - `outputs/qualitative/planb_vs_baseline/planb_vs_planbfeat_full600_step599.mp4`
3. baseline vs planb+feat（整体对照）  
   - `outputs/qualitative/planb_vs_baseline/baseline_vs_planbfeat_full600_step599.mp4`
4. trade-off 口径（短文档，含代表性失败片段）  
   - `notes/protocol_v2_stage2_tradeoff_qual.md`
5. temporal diagnostics（A/B 联合，frame-pair 锚点）
   - A 侧像素域 temporal diff：
     - `outputs/report_pack/diagnostics/temporal_diff_planb_init_600_test_step599.csv`
     - `outputs/report_pack/diagnostics/temporal_diff_planb_feat_v2_full600_test_step599.csv`
     - `outputs/report_pack/diagnostics/temporal_diff_delta_planbfeat_minus_planb_test_step599.csv`
     - `outputs/report_pack/diagnostics/temporal_diff_topk_table_planbfeat_minus_planb_test_step599.md`
   - B 侧 tLPIPS curve：
     - `notes/protocol_v2_tlpips_curve_diagnostics.md`
     - `outputs/report_pack/diagnostics/tlpips_curve_planb_init_600_test_step599.csv`
     - `outputs/report_pack/diagnostics/tlpips_curve_planb_feat_v2_full600_test_step599.csv`
     - `outputs/report_pack/diagnostics/tlpips_curve_delta_planbfeat_minus_planb_test_step599.csv`
     - `outputs/report_pack/diagnostics/tlpips_curve_topk_planbfeat_minus_planb_test_step599.md`

### 动静解耦导出（若已落盘）

- planb_init_600：
  - static：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
  - dynamic：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- planb_feat_v2_full600（A 侧已补齐导出，预算新增已收口）：
  - τ 依据与失败边界：`notes/velocity_stats_planb_feat_v2_full600_start300.md`、`notes/protocol_v2_static_dynamic_tau_planb_feat_v2_full600.md`
  - static τ_low：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.075432/videos/traj_4d_step599.mp4`
  - dynamic τ_low：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.075432/videos/traj_4d_step599.mp4`
  - static τ_high：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.139066/videos/traj_4d_step599.mp4`
  - dynamic τ_high：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.139066/videos/traj_4d_step599.mp4`
  - （补充，便于与 planb 同 τ 对齐）static τ=0.075436：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_static_tau0.075436/videos/traj_4d_step599.mp4`
  - （补充，便于与 planb 同 τ 对齐）dynamic τ=0.075436：`outputs/protocol_v2/selfcap_bar_8cam60f/export_planbfeat_dynamic_tau0.075436/videos/traj_4d_step599.mp4`

### 诊断结论（一句话）

- 当前 stage‑2 属于 **trade-off**：`planb_feat_v2_full600_lam0.005_start300_ramp200_every16` 在 full600 显示 `PSNR↑`，但 `LPIPS/tLPIPS` 未改善；按预算纪律不新增 full600 sweep，转入机理分析与可解释证据补齐。本轮预算未批准，因此不新增 `..._noconf full600`；以 smoke 趋势 + trade-off 定性证据收口。

## 2.6) 2026-02-28 dual-GPU smoke sweep（Owner B / GPU1）

- 新增 runs（均为 `MAX_STEPS=200`，含 seed 标记）：
  - `planb_feat_v2_smoke200_lam0_sanity_s42_gpu1`
  - `planb_feat_v2_smoke200_lam0_sanity_s43_gpu1`
  - `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s42_gpu1`
  - `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_s43_gpu1`
  - `planb_feat_v2_smoke200_lam0.005_start200_ramp50_every16_s42_gpu1`
  - `planb_feat_v2_smoke200_lam0.002_start200_ramp50_every16_s42_gpu1`
  - `planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16_s43_gpu1`（B4 复现）
  - `planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s44_gpu0`（A 可选补 1 seed，用于稳定性判定）
- 噪声带估计（test@step199, 对照 `planb_init_smoke200`）：
  - `|B1-B2|` 的 `tLPIPS` seed 差异：`0.000631`
  - `|B3-B4|` 的 `tLPIPS` seed 差异：`0.000685`
  - 取 `tLPIPS` 噪声带上界 `0.000685`，建议“可置信改善阈值”至少 `> 0.001371`（2x 噪声带）
  - 已同步给 A 侧口径：`tLPIPS` 小于 `0.001371` 的变化优先视为噪声，不作为稳定改善证据
- 讨论/预算触发结论：
  - 当前未满足“同一候选在 ≥2 seeds 同时 `ΔtLPIPS <= 0` 且 `ΔLPIPS <= 0`，且幅度显著大于噪声带”的触发条件
  - 因此 2026-02-28 收口结论为：不申请新增 full600 预算，继续按 mixed trend + 失败分析路径推进
  - framediff(p=0.02) seed 复现结论：`start150_ramp50_every16` 的 seed43 相比 seed42 出现 `ΔPSNR=-0.0040 / ΔLPIPS=+0.0026 / ΔtLPIPS=+0.0004`，稳定性未优于 gating=none，暂不作为预算触发依据。

## 3) 推荐读法（答辩/审计优先）

1. 先看 `scoreboard_full600_vs_v1.md`
   - 用于判断 stage‑2 相对 stage‑1（baseline/planb_init）是否增益、是否命中止损线。
2. 再看 `scoreboard.md` 与 `scoreboard_smoke200.md`
   - 只看 v2 内部对照（smoke200 趋势 + full600 单点结果），用于补齐“可跑+可复现”的证据链。
3. 最后看可解释材料（用于答辩/审计时“解释 VGGT 在看什么、我们在约束什么”）
   - cue/伪掩码证据：`notes/protocol_v2_vggt_cue_viz.md`
   - feature 本体图（PCA->RGB）：`notes/protocol_v2_vggt_feature_pca.md`
   - 稀疏对应可视化：`notes/protocol_v2_sparse_corr_viz.md`

## 4) scoreboard 生成命令

```bash
python3 scripts/build_report_pack.py

# smoke200
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --delta_baseline_run planb_init_smoke200 \
  --stage test \
  --step 199

# full600
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --stage test \
  --step 599

# cross-protocol full600 (v1 vs v2)
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix '' \
  --stage test \
  --step 599
```

## 5) evidence tarball（离线包）与 sha256 manifest

- tarball：`outputs/report_pack_2026-02-28.tar.gz`（由 `python3 scripts/pack_evidence.py` 生成；日期按打包当日滚动）
- manifest：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`（从 tar 内解包落盘的快照）

核对方法（示例）：

1. 查看 tar 内 manifest：
   - `tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv | head`
2. 校验某个文件是否被篡改：
   - 计算文件 sha256，与 `manifest_sha256.csv` 同路径行对比即可。
