# Feature-Loss v2（post-fix）复核与结论收敛 Implementation Plan（Owner A）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在包含 `token_proj` 对齐修复与更保守默认值的最新 `origin/main` 上，以最小 GPU 预算复核 Feature-Loss v2（M1 smoke200 + 选择性 full600），并产出可审计的 Go/No-Go 结论与证据快照（文本入库）。

**Architecture:** 严格遵守 `protocol_v1`；先做对齐的 smoke200（baseline/v2/v2_gated + 小范围 lambda sweep），仅当 smoke200 不灾难且有趋势时才启动 full600（优先 1 次；第 2 次 full600 仅在第 1 次出现正向趋势时允许）。最后刷新 report-pack + evidence（tar.gz 不入库，仅登记 SHA；文本快照入库）。

**Tech Stack:** Bash runners（`scripts/run_train_*.sh`）、FreeTimeGsVanilla trainer、VGGT cache（`scripts/precompute_vggt_cache.py`）、report-pack（`scripts/build_report_pack.py`/`scripts/summarize_scoreboard.py`/`scripts/pack_evidence.py`）。

---

## 前置硬约束（违反即不可比）

- 数据与协议锁死：`docs/protocol.yaml`（-> `docs/protocols/protocol_v1.yaml`）、`data/selfcap_bar_8cam60f`、frames `[0,60)`、cams `02-09`、split train `02-07` / val `08` / test `09`。
- 不改协议项：`global_scale/keyframe_step/image_downscale/densification schedule/seed/camera split` 等任何“训练分布”相关项；如需改，必须升 `protocol_v2` 并重跑 baseline/control（本计划不做）。
- 输出目录纪律：所有新 run 放在 `outputs/protocol_v1/selfcap_bar_8cam60f/<run_name>/`（便于 `metrics.csv/scoreboard.md` 自动收录；run_name 建议带 `postfix`）。
- 不入库大文件：不提交 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只提交 `docs/report_pack/*` 文本快照与 `artifacts/report_packs/SHA256SUMS.txt`。

---

### Task 1: 建立干净执行环境（对齐 main + 记录 provenance）

**Files:**
- Create: `notes/v2_postfix_preflight_owner_a.md`

**Step 1: 新建/切换到干净 worktree（不要复用旧冲突 worktree）**

Run（示例，按你本机习惯即可）：
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-v2-postfix origin/main
cd .worktrees/owner-a-20260226-v2-postfix
```

**Step 2: 记录本次执行的 git 版本（必须写入 notes）**

Run：
```bash
git rev-parse HEAD
git log -n 3 --oneline
```

Expected：HEAD 至少包含 `d1b95b2` 与 `a859078` 之后的版本（即 token_proj 对齐修复 + 保守默认值已在当前代码中）。

**Step 3: 快速健康检查（不跑 GPU）**

Run：
```bash
python3 scripts/tests/test_token_proj_resize_alignment.py
python3 scripts/tests/test_feature_loss_v2_artifacts_exist.py
python3 scripts/tests/test_vggt_cache_contract.py
```

Expected：全部 PASS。

**Step 4: 数据契约检查（避免跑到一半才发现缺 triangulation）**

Run：
```bash
test -d data/selfcap_bar_8cam60f/images
test -d data/selfcap_bar_8cam60f/triangulation
test -d data/selfcap_bar_8cam60f/sparse/0
```

Expected：均返回 0。

---

### Task 2: Gate M1（对齐 smoke200）+ 最小 lambda sweep（只做 smoke200）

**Files:**
- Create: `notes/v2_postfix_m1_owner_a.md`

**Step 1: baseline smoke200（作为 M1 对照真值）**

Run（GPU0 示例）：
```bash
GPU=0 MAX_STEPS=200 \
  RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_postfix \
  bash scripts/run_train_baseline_selfcap.sh
```

Expected：
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_postfix/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_postfix/videos/traj_4d_step199.mp4`

**Step 2: v2 smoke200（使用 runner 新默认：lambda=0.01, ramp=400, layer=17）**

Run：
```bash
GPU=0 MAX_STEPS=200 \
  RESULT_TAG=feature_loss_v2_smoke200_postfix \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```

Expected：同样产出 `stats/test_step0199.json` 与 `videos/traj_4d_step199.mp4`，且 `stats/throughput.json` 存在。

**Step 3: v2_gated smoke200（framediff gate）**

Run：
```bash
GPU=0 MAX_STEPS=200 \
  RESULT_TAG=feature_loss_v2_gated_smoke200_postfix \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```

Expected：
- 产物齐全（同上）
- stdout 中出现：
  - `gating=framediff`
  - `has_gate_framediff=True`
- 且不出现 framediff gate 缺失的降级 warning。

**Step 4: M1 判定（写入 notes）**

判定规则（保守版，满足即可进 full600）：
- v2/v2_gated 的 `PSNR` 不应相对 `baseline_smoke200_postfix` 灾难性下降（建议阈值：`ΔPSNR >= -0.5dB`）
- `tLPIPS` 不应显著变差（建议阈值：`ΔtLPIPS <= +0.01`）
- 吞吐不触发止损：v2 `iter_per_sec` 不低于 baseline 的 0.5 倍（粗即可）

**Step 5: 最小 lambda sweep（只做 2 个点，避免烧 GPU）**

目的：为 full600 选更稳的 knee point（Pareto：PSNR vs tLPIPS）。

Run（两个点即可，示例：0.005 与 0.01；可按情况替换）：
```bash
# lambda=0.005
GPU=0 MAX_STEPS=200 LAMBDA_VGGT_FEAT=0.005 \
  RESULT_TAG=feature_loss_v2_smoke200_postfix_lam0.005 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh

# lambda=0.01（默认；可重复但建议保留一个“显式标注 lambda”的目录，方便审计）
GPU=0 MAX_STEPS=200 LAMBDA_VGGT_FEAT=0.01 \
  RESULT_TAG=feature_loss_v2_smoke200_postfix_lam0.01 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```

Expected：两条 run 都有 `stats/test_step0199.json`，并在 notes 中记录 2 个点的（PSNR, LPIPS, tLPIPS, iter/s）。

---

### Task 3: Gate M2（选择性 full600，最多 1+1 次）

**Files:**
- Create: `notes/v2_postfix_m2_owner_a.md`

**Step 1: 选择 1 个 full600 候选（基于 smoke200 sweep）**

写入 notes：候选的 `lambda/ramp/layer/top_p` 与选择理由（Pareto knee / 退化最小 / tLPIPS 趋势最好）。

**Step 2: 跑 full600（优先跑无 gating 版本作为主判据）**

Run（示例：沿用你选择的 lambda；目录名必须带 postfix）：
```bash
GPU=0 MAX_STEPS=600 LAMBDA_VGGT_FEAT=0.01 \
  RESULT_TAG=feature_loss_v2_postfix_600 \
  bash scripts/run_train_feature_loss_v2_selfcap.sh
```

Expected：
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/stats/test_step0599.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/stats/throughput.json`

**Step 3: full600 快速判定（写入 notes，并决定是否允许第 2 次 full600）**

对比基准（已有）：`baseline_600`、`control_weak_nocue_600`。

- 若出现显著退化（建议阈值：`PSNR` 低于 baseline_600 超过 1dB，或 `tLPIPS` 高于 baseline_600 超过 0.01），直接 stoploss：不跑 gated full600。
- 只有当无 gating full600 出现“可辩护趋势”（例如 tLPIPS 明显下降，且 PSNR/LPIPS 退化可接受）时，才允许跑 gated full600 做对照。

**Step 4（可选，仅在 Step 3 通过时允许）: gated full600**

Run：
```bash
GPU=0 MAX_STEPS=600 LAMBDA_VGGT_FEAT=0.01 \
  RESULT_TAG=feature_loss_v2_gated_postfix_600 \
  bash scripts/run_train_feature_loss_v2_gated_selfcap.sh
```

Expected：同样有 `test_step0599.json` 与 `traj_4d_step599.mp4`。

---

### Task 4: 证据链刷新 + 入库（仅文本）

**Files:**
- Modify: `Progress.md`
- Modify: `artifacts/report_packs/SHA256SUMS.txt`
- Create: `docs/report_pack/2026-02-26-v15/`（若当日已有其他 v15，请顺延 v16）
- Create: `notes/v2_postfix_summary_owner_a.md`

**Step 1: 刷新 report-pack（生成 metrics + scoreboard）**

Run：
```bash
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py
```

Expected：
- `outputs/report_pack/metrics.csv` 新增 postfix run 行
- `outputs/report_pack/scoreboard.md` 出现 `feature_loss_v2*_postfix_600`（若跑了 full600）

**Step 2: 打包 evidence（tar.gz 不入库，只登记 sha）**

Run：
```bash
DATE_TAG=$(date +%F)-v15
OUT_TAR="artifacts/report_packs/report_pack_${DATE_TAG}.tar.gz"
python3 scripts/pack_evidence.py --repo_root . --out_tar "$OUT_TAR"
sha256sum "$OUT_TAR" | tee -a artifacts/report_packs/SHA256SUMS.txt
```

Expected：`SHA256SUMS.txt` 追加 1 行。

**Step 3: 落地 docs 文本快照（入库）**

Run（示例）：
```bash
mkdir -p "docs/report_pack/${DATE_TAG}"
cp -a outputs/report_pack/metrics.csv "docs/report_pack/${DATE_TAG}/"
cp -a outputs/report_pack/scoreboard.md "docs/report_pack/${DATE_TAG}/"
cp -a outputs/report_pack/ablation_notes.md "docs/report_pack/${DATE_TAG}/" || true
cp -a outputs/report_pack/failure_cases.md "docs/report_pack/${DATE_TAG}/" || true
cp -a outputs/report_pack/manifest_sha256.csv "docs/report_pack/${DATE_TAG}/" || true
```

**Step 4: 写结论页并更新 Progress**

写入：
- `notes/v2_postfix_summary_owner_a.md`：给出最终 Go/No-Go（是否继续 v2 / 是否触发 Plan‑B），并明确本次 runs 的 run_dir 列表。
- `Progress.md`：更新“一句话状态”与 v2 进展段，避免覆盖掉 weak/strong/vggt-probe 等既有结论。

**Step 5: 最小回归测试 + 提交**

Run：
```bash
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_pack_evidence.py

git status --porcelain=v1
```

Commit（示例）：
```bash
git add Progress.md notes/v2_postfix_* docs/report_pack/${DATE_TAG} artifacts/report_packs/SHA256SUMS.txt
git commit -m "docs: add v2 post-fix rerun evidence and decision notes (${DATE_TAG})"
git push origin HEAD:main
```

