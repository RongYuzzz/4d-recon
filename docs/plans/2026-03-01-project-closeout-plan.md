# Project Closeout Execution Plan (2026-03-01 -> 2026-03-22)

> 执行方式：严格按 Task 逐项推进；任何会改变训练行为/评测口径的修改都必须落到新协议/新结果目录，避免污染既有证据链。

**Goal:** 在 **2026-03-06** 前完成“可审计证据链 + 关键可信度风险清零 + 可复现交付（Code Freeze）”，并按写作节奏在 **2026-03-22** 定稿。

**Architecture:** 以 `mentor-discussion-brief.md` 为总控、以 `professional-decisions.md` 为不可争辩的拍板约束、以 `suggestions.md` 为并发作战参考；所有新增实验以“新协议/新结果目录”承载，**不回写**既有 `protocol_v1/v2` 证据链。

**Tech Stack:** Bash runners (`scripts/run_train_*.sh`), FreeTimeGsVanilla fork (`third_party/FreeTimeGsVanilla`), report-pack (`scripts/build_report_pack.py`, `scripts/summarize_scoreboard.py`, `scripts/pack_evidence.py`), pytest.

---

## 0. Inputs / Source of Truth (必读，避免重复争论)

- 总控讨论材料（已升级为执行材料）：`docs/reviews/2026-02-28/mentor-discussion-brief.md`
- 专家拍板（必须遵守）：`professional-decisions.md`
- 同行建议（并发/倒排期）：`suggestions.md`
- baseline/论文/上游/fork 偏差（同行补充，回答 baseline 合理性）：`docs/reviews/2026-03-01/baseline-paper-vanilla-deviations-peer-provided.md`
- baseline 风险工作底稿（Top-K 风险聚焦）：`docs/reviews/2026-03-01/freetimegs-paper-vs-freetimegsvanilla-deviations.md`

## 1. Non-Negotiables (不满足直接判失败)

- **不回写旧证据链**：`protocol_v1/v2` 的既有结果目录与 scoreboard 不改不回写；任何“修 bug / 改协议 / 拉长训练”都落到新协议/新目录。
- **baseline 事实定义写死**：baseline 是“协议化 fork 的 FreeTimeGsVanilla（SelfCap bar, 8cam×60f, 固定拆分）”，不是论文 FreeTimeGS 端到端复现。
- **600 steps 不能是唯一支撑**：必须做 `convergence sanity check`（至少 5k；2k/5k step 打点），回答“差距是上限差异还是早期收敛速度差异”。
- **manifest_match 必须为 yes**：最终 evidence tar 内 `manifest_sha256.csv` 必须与 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv` 一致；并且 tar 文件名 + SHA256 必须被记录为 freeze 的 Source of Truth（避免“用错 tar 也能对齐快照”的审计漏洞）。
- **Stage-2 不再 sweep**：只允许 1 次“终极衰减验证”（成功写成策略，失败写成 Failure Analysis），不允许把它变成新一轮 full600 扫参。
- **第二场景/第二段必须补齐**：最低成本也要有一行指标 + 一段视频（anti-cherry-pick）。
- **DoD 必须可指认（内容 + 审计）**：
  - 内容三件套：1 份主 scoreboard（含协议与 step 指示）、1 段定性视频（动静解耦/object removal 或等价演示）、1 张解释性图（trade-off/Pareto/失败边界）。
  - 审计三件套：1 份 evidence tar（含 `git_rev.txt` + `manifest_sha256.csv`）、`manifest_match: yes`、1 页 Runbook。

## 2. Operating Rules (执行纪律，避免把问题越做越大)

- 所有新 run 必须满足“最小可审计产物”：`cfg.yml` + `stats/test_step*.json` + `throughput.json`（runner 已写入）。
- 新协议/新 run 的结果目录必须显式区分：建议统一前缀 `outputs/protocol_v1_convergecheck/...`、`outputs/protocol_v1_calib/...`、`outputs/protocol_v2_final/...`。
- 每个工作日结束必须刷新一次 `outputs/report_pack/metrics.csv` 与相关 scoreboard（只增量追加，不删旧行）。
- 任何可能改变训练行为的代码修复（duration_reg/time normalization 等）：
  - 优先“关掉/绕开”跑出对照（用于回答可信度问题）。
  - 若要修复，必须在新协议里修，并在文档里写清“旧结果仍保留，但存在 limitation”。

---

## 3. Workstreams（资源可切换：2 GPU / 2 人 或 3 GPU / 3 人）

### 推荐：2 人 / 2 GPU（真正“两人都吃 GPU”的稳定分工）

目标：把两条最长的 GPU-heavy 主线拆开并行跑，避免“一个人排队长训、另一个人只能等结果/写文档”。

**核心并行原则（写死）：**
- `convergecheck` 的两条长训 **必须并行**：`baseline_long`（GPU-0） vs `planb_init_long`（GPU-1）。
- `convergecheck` 完成后，`seg300_360`（GPU-1）与 `stage2_decay_final`（GPU-0）**尽量并行**。
- CPU/文档工作（manifest/scoreboard/runbook）穿插在长训期间完成，避免等 GPU。

**Owner A（GPU-0）主线：**
- Task 3：跑 1–2 个 `baseline_smoke200`（校准 sweep 的一部分）
- Task 1.5：输出 `notes/protocol_v1_time_duration_audit.md`（duration_reg + time normalization 风险核验；CPU，可穿插在长训期间）
- Task 4：跑 `baseline_long5k/10k_dur0`（convergecheck baseline 线）
- Task 6：跑 `stage2_decay_final`（**VGGT**；仅在 D1/D2/D4/D5 不被阻塞时执行；否则用 GPU-0 补 `10k` 或补 seeds）
- 夹缝 CPU：Task 7 Runbook 起草（复现命令/产物路径/验收口径）；不运行 pack/scoreboard（默认交给 Owner B 单写者）

**Owner B（GPU-1）主线：**
- Task 3：跑剩余 `baseline_smoke200`（校准 sweep 的一部分）
- Task 4：跑 `planb_init_long5k/10k_dur0`（convergecheck planb 线）
- Task 5：跑 `seg300_360` 的 `baseline_600` → `planb_init_600`（anti-cherry-pick 第二段）
- Task 6.5：输出 `docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`（DoD 资产指认；CPU，冻结前必做）
- 夹缝 CPU：Task 1 manifest_match 清零（与 Owner A 分摊；优先 Day1 做完）
- 夹缝 CPU：Task 7 主表/打包/manifest 快照（单写者默认 B：`build_report_pack.py` / `summarize_scoreboard.py` / `pack_evidence.py`）

**共享文件写入规则（避免互相踩）：**
- 单写者默认：**Owner B** 负责写入/更新（`build_report_pack.py` / `summarize_scoreboard.py` / `pack_evidence.py` 及其产物与快照）。
- `outputs/report_pack/metrics.csv`、`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`、`docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`：同一时间只允许 1 人更新；最终冻结版以 Task 7 为准。

**最小同步点（只保留会卡死后续的点）：**
1. Task 3 结束：拍板 `lambda_4d_reg=<from_task3>`（写进 convergecheck 协议/命令，A/B 必须一致）。
2. Task 4 结束：把结论归类到 A/B/C 三分支，并同步更新写作 claim（避免“长训结果出来后推翻全文”）。
3. Task 7 冻结前：锁定 DoD 资产路径 + `manifest_match: yes`。

### 备选：3 人 / 3 GPU（资源充足时的原始并发）

### Workstream A (GPU-0): Baseline Credibility + Convergence

目标：封死“baseline 不合理 / 欠拟合 / 短训无说服力”两条一票否决线。

### Workstream B (GPU-1): Second Segment / Generalization

目标：补齐 anti-cherry-pick 的第二段证据（最小成本实现开题路线的“多数据/泛化”承诺替代）。

### Workstream C (GPU-2 + CPU): Audit / Packaging + Stage-2 Closure

目标：manifest 清零 + 最终证据包冻结；Stage‑2 做最后一次封棺实验（成功/失败都要可写）。

---

## 4. Tasks (可执行，含文件/命令/验收)

### Task 0: 建立本次 Closeout 的“结果登记表”(5-10 min)

**Files:**
- Create: `docs/reviews/2026-03-01/closeout-log.md`

**Step 1: Create log skeleton**

写入固定字段（每次 run 都要填）：
- date/time, git rev, protocol id, runner command, result_dir, key metrics, pass/fail gate, next action

**Step 2: Commit**

Run:
```bash
git add docs/reviews/2026-03-01/closeout-log.md
git commit -m "docs(closeout): add 2026-03-01 closeout log"
```

验收：log 文件存在且可用于每日同步。

---

### Task 1: `manifest_match` 清零 (P0, Day1)

**Files:**
- Modify: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- Create/Modify: `docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`
- (Optional) Modify: `docs/report_pack/2026-02-27-v2/README.md` (记录最终 tar 名称与校验命令)

**Step 0: Pick an evidence tar name (SoT)**

建议先用“当天日期”命名（便于追踪），例如：`outputs/report_pack_2026-03-01.tar.gz`。

**Step 1: Rebuild metrics.csv**

Run:
```bash
python3 scripts/build_report_pack.py
```

Expected: `outputs/report_pack/metrics.csv` 更新时间刷新。

**Step 2: Repack evidence tar**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-03-01.tar.gz
```

Expected: `outputs/report_pack_2026-03-01.tar.gz` 生成成功。

**Step 3: Preflight check (tar integrity + required entries)**

Run:
```bash
tar -tzf outputs/report_pack_2026-03-01.tar.gz | rg -n "^(manifest_sha256\\.csv|git_rev\\.txt)$" | cat
```

Expected: 至少包含 `manifest_sha256.csv` 与 `git_rev.txt` 两项。

**Step 4: Verify manifest match vs current docs snapshot (hard gate)**

Run:
```bash
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv <(tar -xOzf outputs/report_pack_2026-03-01.tar.gz manifest_sha256.csv)
```

Expected:
- 无论 diff 是否为空：都必须执行 Step 5 记录 tar SHA256（作为 freeze 的 Source of Truth）。
- 若 diff 非空：说明你生成了新的 tar（内容变更/新增结果），必须执行 Step 6 刷新 docs 快照，然后在 Step 7 复核 diff 为空。

**Step 5: Record tar SHA256 (always)**

Run:
```bash
sha256sum outputs/report_pack_2026-03-01.tar.gz | tee docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt
```

Expected: `docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt` 里记录了 tar 的 SHA256 与文件名。

**Step 6: Refresh docs snapshot (only if Step 4 mismatched)**

Run:
```bash
tar -xOzf outputs/report_pack_2026-03-01.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
```

**Step 7: Verify again (must be empty after refresh)**

Run:
```bash
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv <(tar -xOzf outputs/report_pack_2026-03-01.tar.gz manifest_sha256.csv)
```

Expected: diff 为空（exit code 0）。

**Step 8: Commit**

Run:
```bash
git add docs/report_pack/2026-02-27-v2/manifest_sha256.csv docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt
git commit -m "docs(report-pack): lock evidence tar manifest snapshot (2026-03-01)"
```

验收：以后任何人拿 tar 与 docs snapshot 对比均一致。

---

### Task 1.5: Baseline 风险自检闭环（duration_reg + time normalization）(P0, Day1-2)

动机：这两个点会直接影响 baseline 合理性与“短训提升”的可信度，必须在 closeout 期间给出**可审计结论**（修复到新协议或写为 limitation；但不能只有口头解释）。

**Files:**
- Create: `notes/protocol_v1_time_duration_audit.md`

**Step 1: Duration_reg target 语义核验**

写清以下三点（给出代码指针/运行产物路径）：
- `init_duration=-1 (auto)` 时 duration_reg 的 target 取值是什么？是否存在“target=-1 导致永远为正”的风险？
- 若存在风险：本轮 closeout 统一采用 `--lambda-duration-reg 0` 的策略，哪些新协议受影响（calib / convergecheck / seg300_360 / stage2_final）？
- 是否需要/能否在新协议里做最小修复（不回写旧证据链）？

**Step 2: Time normalization / off-by-one 自洽性核验**

写清三处定义是否一致（combine/dataset/trainer），以及结论：
- 若不一致：本轮是否选择“修复对齐到新协议”，还是写为 limitation 并避免 paper-level 对比？
- 若修复：修到哪里、哪些 run 必须重跑（只落新协议/新目录）。

**Step 3: Commit**

Run:
```bash
git add notes/protocol_v1_time_duration_audit.md
git commit -m "docs(audit): add protocol_v1 time/duration risk audit note"
```

验收：导师/审查者能在 1 页内读到“风险是否成立 + 处置策略 + 影响范围”。

---

### Task 2: 让 runner 支持“校准/长训”必要的参数注入 (Day1)

动机：现有 runner 把 `--eval-steps/--save-steps` 固定成 `MAX_STEPS`，不支持 `--lambda-4d-reg` sweep，也不便于统一关闭 `duration_reg`。

**Files:**
- Modify: `scripts/run_train_baseline_selfcap.sh`
- Modify: `scripts/run_train_planb_init_selfcap.sh`
- Modify: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`

**Step 1: Add `EXTRA_TRAIN_ARGS` passthrough (no behavior change when empty)**

目标：允许：
- baseline 校准：`EXTRA_TRAIN_ARGS="--lambda-4d-reg 1e-3 --lambda-duration-reg 0"`
- 长训打点：`EXTRA_TRAIN_ARGS="--eval-steps 600 2000 5000 --save-steps 600 2000 5000"`

**Step 2: Add comma-separated `EVAL_STEPS` / `SAVE_STEPS` env (optional)**

目标：不依赖用户写长串 `EXTRA_TRAIN_ARGS`，例如：
- `EVAL_STEPS=600,2000,5000`
- `SAVE_STEPS=600,2000,5000`

**Step 3: Add `CKPT_PATH` resume support for stage-2 runner**

目标：让 Task 6 的 “phase 续跑衰减”能全部通过 runner 执行（统一 `cfg.yml`/`throughput.json`/`stats` 产物形态），避免手写长命令造成不可审计偏差。

关键审计点（必须覆盖）：
- **trainer 会在每次 `train()` 开始时覆盖写 `RESULT_DIR/cfg.yml`**（见 `third_party/FreeTimeGsVanilla/...:3561-3565`）。多 phase resume 会导致最后一次 phase 的 cfg 覆盖掉前面 phase 的配置。
- 因此 runner 在检测到 `CKPT_PATH` 且 `RESULT_DIR/cfg.yml` 已存在时，必须先做一次 cfg 快照（例如 `cfg_before_resume_from_ckpt_149.yml`），再启动训练。

**Step 4: Add minimal smoke test for runner argument wiring**

目标：新增一个轻量 pytest：用“假 python/假 trainer”捕获 runner 拼出来的 argv，断言 `EXTRA_TRAIN_ARGS` 与 `EVAL_STEPS/SAVE_STEPS` 与（若有）`CKPT_PATH` 正确注入（不跑真实训练）。

Run:
```bash
pytest -q scripts/tests/test_runner_args_passthrough.py
```

Expected: PASS（确保 runner 未被破坏）。

**Step 5: Commit**

Run:
```bash
git add scripts/run_train_baseline_selfcap.sh scripts/run_train_planb_init_selfcap.sh scripts/run_train_planb_feature_loss_v2_selfcap.sh
git commit -m "feat(runners): allow extra train args, multi-step eval/save, and ckpt resume"
```

验收：不改变默认行为，但能支撑后续校准与长训。

---

### Task 3: Baseline 校准 smoke200 sweep (P0, Day2)

**Files:**
- Create: `notes/protocol_v1_baseline_calibration_smoke200.md` (记录命令、结果、结论)
- (Optional) Modify: `docs/reviews/2026-02-28/mentor-discussion-brief.md` (补一句“校准后 baseline 定义”)

**Runs:**
- dataset: `data/selfcap_bar_8cam60f`
- steps: `MAX_STEPS=200`（smoke200）
- 必须统一：`--lambda-duration-reg 0`（先绕开 duration_reg target 歧义）
- sweep knob：`--lambda-4d-reg` in `1e-4/1e-3/1e-2`

**2 GPU 并行建议（避免校准本身变成排队）：**
- GPU-0 跑 `l4d=1e-4`，GPU-1 跑 `l4d=1e-3`，第三个 `l4d=1e-2` 用先空出的那张卡补齐（把 Step 3 里的 `GPU=0` 改成空闲 GPU）。

**Step 1: Run baseline smoke200 (control)**

Run:
```bash
GPU=0 MAX_STEPS=200 RESULT_DIR=outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_l4d1e-4_dur0 \
EXTRA_TRAIN_ARGS="--lambda-4d-reg 1e-4 --lambda-duration-reg 0" \
bash scripts/run_train_baseline_selfcap.sh
```

Expected: `.../stats/test_step0199.json` exists.

**Step 2: Run baseline smoke200 (l4d=1e-3)**

Run:
```bash
GPU=1 MAX_STEPS=200 RESULT_DIR=outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_l4d1e-3_dur0 \
EXTRA_TRAIN_ARGS="--lambda-4d-reg 1e-3 --lambda-duration-reg 0" \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 3: Run baseline smoke200 (l4d=1e-2)**

Run:
```bash
# Run on whichever GPU is free (set GPU=0 or GPU=1)
GPU=0 MAX_STEPS=200 RESULT_DIR=outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_l4d1e-2_dur0 \
EXTRA_TRAIN_ARGS="--lambda-4d-reg 1e-2 --lambda-duration-reg 0" \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 4: Update metrics & scoreboard (smoke200)**

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_calib_smoke200.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_calib/ \
  --stage test \
  --step 199 \
  --baseline_regex "^baseline_smoke200_l4d1e-3"
```

Expected: 新的 scoreboard 文件包含 3 个 baseline_calib runs。

Note: `baseline_regex` 决定了 Δ 的参考系；如果你想把 “control” 定义为 `l4d=1e-4`，就把 regex 改成 `^baseline_smoke200_l4d1e-4`。

**Step 5: Write calibration conclusion**

在 `notes/protocol_v1_baseline_calibration_smoke200.md` 写清：
- “校准后 baseline 选哪个作为 convergecheck 的 baseline 配方”
- 若三者差异很小：说明 baseline 在 200 steps 下对 λ_reg 不敏感（也是结论）
- 若 1e-2 明显更好：说明旧 baseline 可能被配方拖弱（必须在论文里写清）

**Step 6: Commit**

Run:
```bash
git add notes/protocol_v1_baseline_calibration_smoke200.md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_calib_smoke200.md
git commit -m "docs: add baseline calibration smoke200 sweep results"
```

验收：baseline 可信度攻击面被“最小校准证据”封死。

---

### Task 3.5: Smoke200 噪声带（2 seeds，最小统计防守）(P1, Day2-3)

动机：避免把 seed 噪声当收益；至少给出一个“同向改善 + 超过噪声带”的最小防守口径。

**Files:**
- Create: `notes/protocol_v1_smoke200_seed_noise_band.md`

**Runs (minimal):**
- 固定同一套超参（建议用 Task 3 选出的 `lambda_4d_reg`），对 baseline_smoke200 额外跑 2 个 seed（例如 41/43）。

Run (example):
```bash
GPU=0 MAX_STEPS=200 SEED=41 RESULT_DIR=outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_seed41_dur0 \
EXTRA_TRAIN_ARGS="--lambda-4d-reg <from_task3> --lambda-duration-reg 0" \
bash scripts/run_train_baseline_selfcap.sh

GPU=1 MAX_STEPS=200 SEED=43 RESULT_DIR=outputs/protocol_v1_calib/selfcap_bar_8cam60f/baseline_smoke200_seed43_dur0 \
EXTRA_TRAIN_ARGS="--lambda-4d-reg <from_task3> --lambda-duration-reg 0" \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 1: Summarize**

把两次 seed 的 PSNR/LPIPS/tLPIPS 波动范围写进 `notes/protocol_v1_smoke200_seed_noise_band.md`，作为后续“显著改善”的最小阈值参考。

**Step 2: Commit**

Run:
```bash
git add notes/protocol_v1_smoke200_seed_noise_band.md
git commit -m "docs: add smoke200 2-seed noise band note"
```

---

### Task 4: Convergence sanity check (baseline vs planb_init) (P0, Day3-4)

**Files:**
- Create: `docs/protocols/protocol_v1_convergecheck.yaml` (新协议，明确 max/eval/save steps 与 dur0)
- Create: `docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck.md`
- Create: `notes/protocol_v1_convergecheck_results.md`

**Runs:**
- max_steps: `5000`（最低交付，能到 `10000` 更好）
- eval/save steps: `600,2000,5000`（若 10k：追加 `10000`）
- 必须统一：`--lambda-duration-reg 0`（除非已修复并验证 target 语义）
- baseline 配方：来自 Task 3 的校准结论（至少包含 `lambda_4d_reg` 量级；记录在 convergecheck 协议里，baseline/planb 两个 run 必须用同一套 λ）

**Step 1: Create new protocol YAML**

写入：
- dataset id, camera split, max_steps, eval_steps, save_steps, fixed seeds（建议 42）
- baseline 定义与 limitation（明确非论文复现）

**Step 2: Run baseline_long**

Run (example 5k):
```bash
GPU=0 MAX_STEPS=5000 RESULT_DIR=outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/baseline_long5k_dur0 \
EVAL_STEPS=600,2000,5000 SAVE_STEPS=600,2000,5000 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg <from_task3>" \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 3: Run planb_init_long**

2 GPU 版本：Step 2 与 Step 3 **并行启动**（baseline 在 GPU-0，planb 在 GPU-1），保证两条长训不互相排队。

Run:
```bash
GPU=1 MAX_STEPS=5000 RESULT_DIR=outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/planb_init_long5k_dur0 \
PLANB_OUT_DIR=outputs/plan_b/selfcap_bar_8cam60f_convergecheck_long5k_dur0 \
EVAL_STEPS=600,2000,5000 SAVE_STEPS=600,2000,5000 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg <from_task3>" \
bash scripts/run_train_planb_init_selfcap.sh
```

Expected: `stats/test_step0599.json`, `stats/test_step1999.json`, `stats/test_step4999.json` 均存在。

**Step 4: Build report pack + summarize (multi-step)**

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_convergecheck/ \
  --stage test \
  --step 599 \
  --baseline_regex "^baseline_"
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck_step2000.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_convergecheck/ \
  --stage test \
  --step 1999 \
  --baseline_regex "^baseline_"
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck_step5000.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_convergecheck/ \
  --stage test \
  --step 4999 \
  --baseline_regex "^baseline_"
```

Note: 若 convergecheck 目录里出现多个 baseline run（例如 long5k/long10k 或多 seed），务必把 `baseline_regex` 写成**精确匹配**（例如 `^baseline_long5k_`），避免脚本按字典序选错 baseline。

**Step 5: Write conclusion (关键回答句必须写出来)**

在 `notes/protocol_v1_convergecheck_results.md` 写清三种可能结论与对应写法：
- A: gap 保持/扩大 -> “方法提升不只是早期收敛差异”
- B: gap 收敛到 0 -> “方法主要提升早期收敛/避免局部最优（anytime）”，并在论文里把主张改成“training efficiency / robustness”
- C: gap 反转 -> 必须解释与止损（例如 baseline 校准后过强、planb 初始化对长期上限无益等）

**Step 6: Commit**

Run:
```bash
git add docs/protocols/protocol_v1_convergecheck.yaml docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck*.md notes/protocol_v1_convergecheck_results.md
git commit -m "docs: add protocol_v1 convergecheck plan and results scaffolding"
```

验收：直接回答“短训是否有说服力”问题，避免被合理否定。

---

### Task 5: 第二段（anti-cherry-pick）最小对照 (P1, Day1-4)

优先选用已就绪数据：`data/selfcap_bar_8cam60f_seg300_360`（已含 `images/` + `triangulation/`）。

**Files:**
- Create: `notes/protocol_v1_seg300_360_baseline_vs_planb.md`
- Create: `docs/report_pack/2026-02-27-v2/scoreboard_seg300_360_full600.md`

**Step 1: Run baseline_600 on seg300_360**

Run:
```bash
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 GPU=1 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg <from_task3>" \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 2: Run planb_init_600 on seg300_360**

Note: when `DATA_DIR` != default, **do not reuse** the canonical baseline init NPZ from `selfcap_bar_8cam60f`.
Point `BASELINE_INIT_NPZ` to the baseline init produced in Step 1, otherwise Plan‑B init may silently use the wrong template.

Run:
```bash
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 GPU=1 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600 \
BASELINE_INIT_NPZ=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600/keyframes_60frames_step5.npz \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg <from_task3>" \
bash scripts/run_train_planb_init_selfcap.sh
```

**Step 3: Update metrics & scoreboard**

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_seg300_360_full600.md \
  --select_contains selfcap_bar_8cam60f_seg300_360 \
  --select_prefix outputs/protocol_v1_seg300_360/ \
  --stage test \
  --step 599
```

**Step 4: Collect one qualitative video**

验收：至少拿到两段 `videos/traj_4d_step599.mp4`（baseline vs planb），并在 note 里写出路径。

**Step 5: Commit**

Run:
```bash
git add notes/protocol_v1_seg300_360_baseline_vs_planb.md docs/report_pack/2026-02-27-v2/scoreboard_seg300_360_full600.md
git commit -m "docs: add seg300_360 baseline vs planb minimal generalization evidence"
```

---

### Task 6: Stage-2 终极衰减验证（封棺，不 sweep）(P1, Day3-4)

建议用“分段 resume”实现衰减（避免修改 trainer core）：在同一 result_dir 下连续训练，多次 resume 续跑，逐段降低 `--lambda-vggt-feat`，最后归零交给 photometric。所有 phase 必须：
- 从 phase0 起就统一 `--lambda-duration-reg 0`（除非 Task 1.5 结论认为 duration_reg 已修复并验证）。
- 使用同一个结果目录前缀（建议 `outputs/protocol_v2_final/...`），避免污染既有 `protocol_v2` 证据链。

**Files:**
- Create: `notes/protocol_v2_stage2_decay_final.md`
- Create: `docs/report_pack/2026-02-27-v2/scoreboard_stage2_decay_final.md`

**(Optional but recommended) Step 0: smoke200 trend check (only if budget is tight)**

动机：遵守“最多 1–2 次封棺 run”的纪律；若 smoke200 仍无趋势，不要直接烧 full600。

建议把 600-step 的 4-phase schedule 等比例缩短到 200 steps（每段 50 steps），跑完后只看趋势：
- phase0: steps 0-49, `lambda=0.005`
- phase1: steps 50-99, `lambda=0.00125`
- phase2: steps 100-149, `lambda=0.0003125`
- phase3: steps 150-199, `lambda=0.0`

若趋势成立再进入 full600；否则把失败写进 Failure Analysis 并 stop.

**Step 1: Decide one decay schedule (write it down before running)**

建议（600 steps）：
- phase0: steps 0-149, `lambda=0.005`
- phase1: steps 150-299, `lambda=0.00125`
- phase2: steps 300-449, `lambda=0.0003125`
- phase3: steps 450-599, `lambda=0.0`

**Step 2: Run phase0 (max_steps=150)**

Run:
```bash
# 2 GPU: use GPU=0. 3 GPU: prefer GPU=2 to avoid blocking convergecheck.
GPU=0 MAX_STEPS=150 RESULT_DIR=outputs/protocol_v2_final/selfcap_bar_8cam60f/planb_feat_v2_decay_final \
PLANB_OUT_DIR=outputs/plan_b/selfcap_bar_8cam60f_stage2_decay_final \
LAMBDA_VGGT_FEAT=0.005 VGGT_FEAT_START_STEP=0 VGGT_FEAT_RAMP_STEPS=0 VGGT_FEAT_EVERY=16 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg <from_task3>" \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected: `.../ckpts/ckpt_149.pt` exists.

**Step 3: Run phase1 resume (max_steps=300)**

Run (requires Task 2: runner supports `CKPT_PATH`):
```bash
# 2 GPU: use GPU=0. 3 GPU: prefer GPU=2 to avoid blocking convergecheck.
GPU=0 MAX_STEPS=300 RESULT_DIR=outputs/protocol_v2_final/selfcap_bar_8cam60f/planb_feat_v2_decay_final \
CKPT_PATH=outputs/protocol_v2_final/selfcap_bar_8cam60f/planb_feat_v2_decay_final/ckpts/ckpt_149.pt \
PLANB_OUT_DIR=outputs/plan_b/selfcap_bar_8cam60f_stage2_decay_final \
LAMBDA_VGGT_FEAT=0.00125 VGGT_FEAT_START_STEP=0 VGGT_FEAT_RAMP_STEPS=0 VGGT_FEAT_EVERY=16 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg <from_task3>" \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

重复 phase2/phase3（改 `MAX_STEPS` 与 `LAMBDA_VGGT_FEAT`，`CKPT_PATH` 指向最新 ckpt）：
- phase2: `MAX_STEPS=450`, `LAMBDA_VGGT_FEAT=0.0003125`, `CKPT_PATH=.../ckpt_299.pt`
- phase3: `MAX_STEPS=600`, `LAMBDA_VGGT_FEAT=0.0`, `CKPT_PATH=.../ckpt_449.pt`

**Step 4: Summarize result**

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_stage2_decay_final.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v2_final/ \
  --stage test \
  --step 599
```

**Step 5: Decide success/failure and lock narrative**

在 `notes/protocol_v2_stage2_decay_final.md` 写清：
- 是否满足成功线：相对 `planb_init_600`，`tLPIPS` 明显改善且 `LPIPS` 不退步（并超过 smoke200 噪声带阈值）
- 若失败：明确写成“语义平滑与高频纹理拟合冲突”的证据链，并停止 stage‑2 追加预算

**Step 6: Commit**

Run:
```bash
git add notes/protocol_v2_stage2_decay_final.md docs/report_pack/2026-02-27-v2/scoreboard_stage2_decay_final.md
git commit -m "docs: add stage-2 final decay experiment plan/result placeholders"
```

---

### Task 6.5: DoD 定性视频 + 解释性图（指认与打包）(P1, Day4-5)

动机：`mentor-discussion-brief.md` 的 DoD 里明确要求“定性视频 + 一页解释性图”；必须在 closeout 期把**具体文件路径**写死，避免临场翻目录。

**Files:**
- Create: `docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`

**Step 1: Lock qualitative video paths**

优先选择与最终主结论一致的模型（例如 `planb_init_600` 或 stage‑2 final），并在 `closeout_dod_assets.md` 写入：
- static-only 视频路径
- dynamic-only 视频路径
- （若有）object removal 或等价演示的视频路径/关键帧

参考已有资产（可直接复用并写明 limitation）：
- `notes/protocol_v2_static_dynamic_tau.md`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_*_tau*/videos/traj_4d_step599.mp4`

**Step 2: Lock one explanatory figure**

从 `outputs/report_pack/diagnostics/` 选择 1 张最能解释 trade-off/失败边界的图（或生成一张新的），并在 `closeout_dod_assets.md` 写入路径与一句话解读。

**Step 3: Verify included in evidence tar**

Run:
```bash
# If the final tar is not built yet, run this after Task 7 / Step 2.
tar -tzf outputs/report_pack_2026-03-06.tar.gz | rg -n "^(outputs/report_pack/diagnostics/|outputs/protocol_v2|outputs/protocol_v2_final|notes/|docs/report_pack/2026-02-27-v2/closeout_dod_assets\\.md)" | head -n 50
```

**Step 4: Commit**

Run:
```bash
git add docs/report_pack/2026-02-27-v2/closeout_dod_assets.md
git commit -m "docs(closeout): lock DoD qualitative assets pointers"
```

---

### Task 7: Code Freeze 打包与 Runbook（3/5 之前完成）

**Files:**
- Create: `docs/runbook/reproduce_code_freeze_2026-03-06.md`
- Create: `docs/report_pack/2026-02-27-v2/scoreboard_code_freeze_2026-03-06.md`
- Modify: `docs/reviews/2026-02-28/mentor-discussion-brief.md`（补 link 到 runbook + 最终 tar）
- Modify: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
- Modify: `docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`

**Step 1: Write Runbook**

必须包含：
- 复现 baseline_600 / planb_init_600 / convergecheck / seg300_360 / stage2_final（若有）的最小命令
- 预期产物路径（`cfg.yml` / `stats` / `videos` / scoreboard）
- `pack_evidence.py` 的最终 tar 名称与 `manifest_match` 校验命令

**Step 1.5: Build freeze "main scoreboard" (single entry point)**

目标：生成一份“主表”用于 DoD（把其它分散的 scoreboard 当作附录/支撑材料）。

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_code_freeze_2026-03-06.md \
  --protocol_id code_freeze_2026-03-06 \
  --select_contains selfcap_bar_8cam60f/ \
  --select_prefix "" \
  --stage test \
  --step 599
```

说明：
- 若需要把 convergecheck/seg300_360 的结果也纳入同一份主表，建议把它们作为第二/第三个 section（用独立表格或链接到对应 scoreboard 文件），并在标题中显式标注 step 与数据段。
- `--select_contains` 是子串匹配：用 `selfcap_bar_8cam60f/`（带 `/`）可以避免误包含 `selfcap_bar_8cam60f_seg300_360`。

**Step 1.6: Curate the main scoreboard (keep it minimal + link out)**

目标：让 `scoreboard_code_freeze_2026-03-06.md` 成为 DoD 的**单入口**，避免现场翻多个文件。

建议在该文件末尾追加一个 “See Also” 小节，至少包含以下指针（按你实际产物路径更新）：
- baseline 校准 sweep：`docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_calib_smoke200.md`
- convergecheck：`docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck*.md`
- 第二段/第二场景：`docs/report_pack/2026-02-27-v2/scoreboard_seg300_360_full600.md`
- stage‑2 final（若有）：`docs/report_pack/2026-02-27-v2/scoreboard_stage2_decay_final.md`
- DoD 资产指针：`docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`

**Step 2: Final evidence tar + snapshot**

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-03-06.tar.gz
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv <(tar -xOzf outputs/report_pack_2026-03-06.tar.gz manifest_sha256.csv) || true
tar -xOzf outputs/report_pack_2026-03-06.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
sha256sum outputs/report_pack_2026-03-06.tar.gz | tee docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv <(tar -xOzf outputs/report_pack_2026-03-06.tar.gz manifest_sha256.csv)
```

Expected: diff 为空。

**Step 3: Commit**

Run:
```bash
git add docs/runbook/reproduce_code_freeze_2026-03-06.md docs/report_pack/2026-02-27-v2/manifest_sha256.csv docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt docs/reviews/2026-02-28/mentor-discussion-brief.md docs/report_pack/2026-02-27-v2/scoreboard_code_freeze_2026-03-06.md
git commit -m "docs: add 2026-03-06 code freeze runbook and lock manifest"
```

验收：任何人按 Runbook 都能复现实验并校验 evidence tar。

---

## 5. Writing Schedule (你给的节奏 -> 具体落地清单)

### 2026-03-01 -> 2026-03-06 (Code Freeze)

- 目标：把“可信度问题”用实验闭环回答掉（baseline 校准 + convergecheck + 第二段），并锁定可审计 evidence。
- 产物：DoD 六件套（见 `mentor-discussion-brief.md` §8.1）。

### 2026-03-06 -> 2026-03-11 (边写边补实验)

**Files:**
- Modify: `docs/writing/planb_paper_outline.md`
- Modify: `docs/writing/planb_qa_cards_v26.md`

写作优先级（先把“会被追问的问题”写死）：
- baseline 定义与 limitation（引用偏差清单 A/B/C 的关键点）
- convergence sanity check 结论与写法（A/B/C 三分支）
- anti-cherry-pick 第二段结论（即使失败也要写成边界）
- stage‑2 的最终结论（成功写策略；失败写 failure analysis）

### 2026-03-12 (初稿)

验收：通篇可以读通，图表与路径一致；任何关键数字都能在 `docs/report_pack/...` 追溯到真源。

### 2026-03-13 -> 2026-03-21 (润色 + 必要补实验)

只允许补“能解决一个明确质疑”的实验；禁止发散探索。

### 2026-03-22 (定稿)

验收：文字、图表、引用路径、复现命令与 evidence tar 全部一致。

---

## 6. Decision Gates (需要导师/专家现场拍板的点)

1. convergecheck 的结论属于 A/B/C 哪一类？对应论文主张是否需要改写为“收敛加速/鲁棒性”？
2. 第二段是否接受 seg300_360 作为 anti-cherry-pick，还是必须换“完全不同场景”？
3. stage‑2 final decay 若仍 trade-off：是否正式停止 stage‑2 并把负结果写成边界（不再追求双赢）？
4. duration_reg / time normalization 的风险：修复到新协议，还是写成 limitation 并避免 paper-level 对比？
