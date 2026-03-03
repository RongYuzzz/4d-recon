# Owner B (GPU1) protocol_v2 GPU + Packaging Follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 GPU1 上补齐 `protocol_v2` 的最小追加证据（只允许 smoke200）并完成 “证据链收口 + 防误读 + 离线包可审计” 的打包与文档同步；尤其修复一个审计风险：离线 tarball 目前不包含 `notes/protocol_v2_framediff_gate_viz.md` 引用的 `outputs/viz/gate_framediff/...` overlay 图片。

**Architecture:** 训练侧严格 timebox（最多 1 个 smoke200 seed 补跑，且不新增 full600）；文档/打包侧以 `docs/report_pack/2026-02-27-v2/README.md` 的生成命令为真源，所有更新通过 `build_report_pack + summarize_scoreboard + pack_evidence + manifest 回填` 闭环。

**Tech Stack:** bash、`python3`、`third_party/FreeTimeGsVanilla/.venv/bin/python`、`scripts/run_train_planb_feature_loss_v2_selfcap.sh`、`scripts/build_report_pack.py`、`scripts/summarize_scoreboard.py`、`scripts/pack_evidence.py`。

---

## Constraints / Invariants（必须遵守）

- 仅使用 **GPU1**：新增训练命令必须显式 `GPU=1`（或 `CUDA_VISIBLE_DEVICES=1`）。
- 不新增 full600：除非仓库出现新的预算决议文件（并在验收里引用路径）。
- 新增训练仅 smoke200：必须显式 `MAX_STEPS=200`，产物目录必须有 `cfg.yml` + `stats/test_step0199.json`。
- 所有新产物仅写入 `outputs/protocol_v2/...`，不覆盖 `protocol_v1/v26`。
- 离线证据包与 `manifest_sha256.csv` 必须覆盖“文档提到的关键路径”（避免审计时出现“文档引用但包里没有”）。

---

### Task 0: Preflight（10 分钟）

**Files:**
- Read: `third_party/FreeTimeGsVanilla/.venv/bin/python`
- Read: `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
- Read: `outputs/report_pack/metrics.csv`

**Step 1: 确认 GPU1 可用**

Run: `nvidia-smi -L`  
Expected: 存在 GPU 1（32GB）。

**Step 2: 确认 venv 与 cache 存在**

Run:
```bash
ls -la third_party/FreeTimeGsVanilla/.venv/bin/python
ls -la outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz
```
Expected: 文件存在。

---

### Task 1（GPU1，最多 1 次，timebox=1h）: 补 1 个 smoke200 seed（noconf 候选稳定性）

**动机：**当前 smoke200 里 `..._noconf` 是“最接近不退步”的候选之一；补 1 个 seed 用于判断是否只是噪声带内波动。

**Files:**
- Create: `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s43_gpu1/`
- Update: `docs/report_pack/2026-02-27-v2/README.md`（新增 run 列表）

**Step 1: 跑 smoke200（seed=43, GPU1, noconf）**

Run:
```bash
VENV_PYTHON=third_party/FreeTimeGsVanilla/.venv/bin/python \
GPU=1 MAX_STEPS=200 SEED=43 \
RESULT_TAG=planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s43_gpu1 \
LAMBDA_VGGT_FEAT=0.005 \
VGGT_FEAT_START_STEP=150 \
VGGT_FEAT_RAMP_STEPS=50 \
VGGT_FEAT_EVERY=16 \
VGGT_FEAT_PHI_NAME=token_proj \
VGGT_FEAT_LOSS_TYPE=cosine \
VGGT_FEAT_GATING=none \
VGGT_FEAT_USE_CONF=0 \
VGGT_CACHE_TAG=selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4 \
VGGT_FEAT_CACHE_NPZ=outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected artifacts:
- `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_smoke200_lam0.005_start150_ramp50_every16_noconf_s43_gpu1/cfg.yml`
- `.../stats/test_step0199.json`

**Step 2: 记录“是否触发预算讨论”的一句话结论**

规则（沿用 v2 README 噪声带口径）：
- 若仍未满足 “≥2 seeds 同时 `ΔtLPIPS<=0` 且 `ΔLPIPS<=0` 且幅度显著大于噪声带” → 明确写：**不触发新增 full600 预算讨论**。

把这句话补进 `docs/report_pack/2026-02-27-v2/README.md` 的 dual-GPU 小节（只需 1-2 行）。

---

### Task 2（No-GPU）: 刷新 metrics.csv + scoreboard（15 分钟）

**Files:**
- Modify: `outputs/report_pack/metrics.csv`
- Modify: `docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md`
- Modify: `docs/report_pack/2026-02-27-v2/scoreboard.md`
- Modify: `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

**Step 1: 刷新 report_pack（metrics.csv）**

Run:
```bash
python3 scripts/build_report_pack.py
```
Expected: `outputs/report_pack/metrics.csv` 更新时间更新，且包含新 run 行。

**Step 2: 生成 smoke200 scoreboard（Δ vs planb_init_smoke200）**

Run:
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --delta_baseline_run planb_init_smoke200 \
  --stage test \
  --step 199
```
Expected: Δ 列不再是 `-`，并包含新 run。

**Step 3: 生成 full600 scoreboard（v2 内部）与 cross-protocol**

Run:
```bash
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2/ \
  --stage test \
  --step 599

python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix '' \
  --stage test \
  --step 599
```

---

### Task 3（No-GPU，必须）: 修复离线包缺失 framediff overlay 的审计风险（TDD，30-45 分钟）

**问题：**`notes/protocol_v2_framediff_gate_viz.md` 引用 `outputs/viz/gate_framediff/.../*.png`，但当前 `outputs/report_pack_2026-02-28.tar.gz` 不包含这些文件（离线审计会断链）。

**目标：**让 `scripts/pack_evidence.py` 把 `outputs/viz/gate_framediff/**` 纳入 tarball（仅此子树，避免把整个 `outputs/viz` 打进去）。

**Files:**
- Modify: `scripts/pack_evidence.py`
- Create: `scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py`

**Step 1: 写一个失败单测（先红）**

Create `scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py`，思路：
- 在 repo 内创建一个临时文件：`outputs/viz/gate_framediff/_test_dummy.png`
- 调用 `scripts.pack_evidence.collect_files(repo_root)`，断言返回列表包含该路径
- 测试结束清理该 dummy 文件

Run: `pytest -q scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py`  
Expected: FAIL（当前不包含该路径）。

**Step 2: 最小改动实现（让测试变绿）**

在 `scripts/pack_evidence.py:collect_files()` 增加：
- 若 `outputs/viz/gate_framediff` 存在：打包 `**/*.png` + `**/*.csv` + `**/*.txt`
- 保持过滤规则不变（仍排除 `ckpts/tb/renders`）

**Step 3: 运行 tests**

Run: `pytest -q`  
Expected: PASS。

**Step 4: Commit（只提交 test + pack_evidence 逻辑）**

Run:
```bash
git add scripts/pack_evidence.py scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py
git commit -m "chore(evidence): include gate_framediff overlays in pack"
```

---

### Task 4（No-GPU，必须）: 重打离线证据包 + 回填 manifest（15 分钟）

**Files:**
- Modify: `outputs/report_pack_2026-02-28.tar.gz`
- Modify: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

**Step 1: 重打 tarball（覆盖同名）**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
```

**Step 2: 回填 manifest 快照**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```

**Step 3: 抽查 tar 内包含 framediff overlay（关键断言）**

Run:
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/viz/gate_framediff/\" | head
```
Expected: 至少出现 1 条路径（证明断链修复）。

---

### Task 5（No-GPU）: 文档同步与收口（20 分钟）

**Files:**
- Modify: `docs/report_pack/2026-02-27-v2/README.md`
- Modify: `docs/reviews/2026-02-27/acceptance-2026-02-27.md`
- Optional: `Progress.md`（只在结论有变化时）

**Step 1: 更新 report-pack README（dual-GPU 小节）**

在 `docs/report_pack/2026-02-27-v2/README.md`：
- 追加新 run tag（Task 1 的 noconf seed）
- 保持结论口径：不触发新增 full600
- 更新 evidence tarball 指针：仍为 `outputs/report_pack_2026-02-28.tar.gz`

**Step 2: 更新验收记录（新增一条 follow-up intake）**

在 `docs/reviews/2026-02-27/acceptance-2026-02-27.md` 追加一小节：
- Intake：列出新增 run tag
- Evidence：引用最新 tarball + manifest 快照
- Conclusion：PASS；并明确不触发新增 full600

**Step 3: Commit（只提交文档同步）**

Run:
```bash
git add docs/report_pack/2026-02-27-v2/README.md \
  docs/report_pack/2026-02-27-v2/scoreboard_smoke200.md \
  docs/report_pack/2026-02-27-v2/scoreboard.md \
  docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md \
  docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  docs/reviews/2026-02-27/acceptance-2026-02-27.md
git commit -m "docs(protocol_v2): update smoke scoreboard and offline bundle pointers"
```

---

## Handoff（给 A 的同步点）

- 若 A 按 `docs/plans/2026-02-28-owner-a-protocol-v2-gpu-followup-plan.md` 新增导出视频或 gate 诊断目录：
  - 等 A 给出最终路径后，再执行一次 Task 4 重打 tarball + 回填 manifest（保证离线包包含 A 的新增产物）。

