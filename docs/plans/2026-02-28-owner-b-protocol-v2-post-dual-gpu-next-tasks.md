# protocol_v2 Post Dual-GPU Smoke Next Tasks (Owner B / GPU1 + No-GPU)

日期：2026-02-28  
前置结论：dual‑GPU smoke200 已完成噪声带估计与当日 scoreboard/README 回填，但当前仍未触发新增 full600 预算讨论；后续以“证据链收口 + 防误读 + 离线包更新”为主。

本文件仅列 Owner B 的后续任务（可与 Owner A 并行）。

---

## 不变量 / 纪律（必须遵守）

1. 不新增 full600（除非形成新的预算决议文件）。
2. 允许新增训练仅限 smoke200，且必须显式写 `GPU=1 MAX_STEPS=200`；无必要不再扩展 sweep。
3. 离线证据包与 `manifest_sha256.csv` 必须覆盖当天新增产物（避免“文档提到但包里没有”的审计风险）。

---

## Task B1（必须）：重打离线证据包 + 回填 manifest（覆盖 15:20 新 runs）

**动机**：当前 `outputs/report_pack_2026-02-28.tar.gz` 与 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv` 的时间在 01:04，无法包含 15:20 之后新增的 dual‑GPU smoke runs 与 framediff cache。

**要做什么**：
1) 重打 tarball（覆盖同名即可）：
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
```
2) 从 tar 内解包并回填 manifest 快照：
```bash
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```
3) 抽查 tar 内包含关键新增项（至少 3 个路径存在即可）：
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"planb_feat_v2_smoke200_lam0_sanity_s42_gpu1/stats/test_step0199\\.json|planb_feat_v2_smoke200_framediff_p0\\.02_lam0\\.005_start150_ramp50_every16/stats/test_step0199\\.json|vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/meta\\.json\" -n
```

**Done**：tarball 已更新且 manifest 回填完成；抽查通过。

---

## Task B2（必须）：补一条“dual‑GPU smoke sweep”验收记录（避免口径漂移）

**要做什么**：
- 在 `docs/reviews/2026-02-27/acceptance-2026-02-27.md` 追加新小节（建议编号 8）：
  - Intake：列出 A1/A2/A3 与 B1~B6 的 run tag（无需贴指标）
  - 指标收口：引用 `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md` 与 `docs/report_pack/2026-02-27-v2/README.md` 的 dual‑GPU 小节
  - 离线包：引用 `outputs/report_pack_2026-02-28.tar.gz` 与 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
  - 结论：PASS；并明确“不触发新增 full600 预算讨论”

**Done**：验收文件新增一节且结论 PASS。

---

## Task B3（推荐，No‑GPU）：让 smoke scoreboard 能显示“Δ vs planb_init_smoke200”

**动机**：当前 `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md` 的 Δ 列为 `-`（因为脚本默认 delta 基线是 `baseline_600`，而 smoke200 的参考应是 `planb_init_smoke200`）。这会让后续审计阅读成本偏高。

**要做什么（最小改动）**：
1) 升级 `scripts/summarize_scoreboard.py`：
   - 新增参数：`--delta_baseline_run`（例如 `planb_init_smoke200`）
   - 当该参数提供时：在读 `metrics.csv` 时**额外查找**同 `stage/step/contains` 的该 baseline 行（忽略 `select_prefix` 限制），用其指标作为 Δ 基线。
2) 更新 `docs/report_pack/2026-02-27-v2/README.md` 的 smoke200 生成命令，增加：
   - `--delta_baseline_run planb_init_smoke200`
3) 新增一个最小单测（`scripts/tests/`）：
   - 在一个临时 metrics.csv（仅几行）里构造 baseline 行 + 1 个 v2 run 行
   - 断言输出 markdown 中 Δ 列不再是 `-`。

**Done**：smoke scoreboard 的 Δ 列可直接读出 “vs planb_init_smoke200”。

---

## Task B4（可选，GPU1 timebox 1h）：补 1 个 framediff(p=0.02) 的 seed 复现

**动机**：A 侧 framediff(p=0.02) 目前只有 seed=42；补 1 个 seed=43 可快速判断它是否比 gating=none 更稳（尤其 tLPIPS 方差）。

**Run（仅 1 次 smoke200）**：
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=43 \
RESULT_TAG=planb_feat_v2_smoke200_framediff_p0.02_lam0.005_start150_ramp50_every16_s43_gpu1 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=framediff \
VGGT_FEAT_GATING_TOP_P=0.02 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

**Done**：产物齐（cfg+stats+throughput），并在 README 的 dual‑GPU 小节补 1 行 “framediff seed 复现结论”（不需要展开长文）。

