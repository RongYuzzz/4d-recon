# Plan-B + Weak Synergy Smoke200 (Owner A) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不新增任何 full600 预算的前提下，用 smoke200 验证 “Plan‑B init + weak cue 注入” 是否存在可复现的正向趋势（或明确仍为负结果），并形成可交接给 B 的写作/打包证据与 Go/No‑Go 结论。

**Architecture:** 复用 `protocol_v1` 的数据与训练超参（seed/global_scale/keyframe_step/cam split 不变），仅将 `--init-npz-path` 指向 `outputs/plan_b/.../init_points_planb_step5.npz`，并分别跑：
1) Plan‑B baseline（已存在：`planb_init_smoke200`）；
2) Plan‑B + 控制组（zeros mask，验证 weak 路径本身不引入差异）；
3) Plan‑B + ours‑weak（diff mask，验证 cue 是否在“物理 init 已修正”时仍负增益）。
全程只做 smoke200（200 steps）；任何 full600 需新决议扩预算。

**Tech Stack:** FreeTimeGsVanilla trainer（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`）、Plan‑B init（`outputs/plan_b/...`）、pseudo masks（`outputs/cue_mining/.../pseudo_masks.npz`）、吞吐统计（`scripts/write_throughput_json.py`）、smoke200 分析（`scripts/analyze_smoke200_m1.py`）。

---

## 约束（必须遵守）

- 仅用 GPU0（32GB）。
- 不改 `docs/protocols/protocol_v1.yaml` 与 canonical 数据口径（相机划分/seed/global_scale/keyframe_step 固定）。
- 不新增任何 full600（只允许 `MAX_STEPS=200`；若需要 full600，必须先新增 `docs/decisions/*` 并明确扩预算）。
- 不提交 `data/`、`outputs/`；只提交 `notes/`（必要时更新 `Progress.md`）。

---

### Task 1: 预检 + 依赖路径核验（No-GPU）

**Files:**
- Modify: (none)
- Create: (none)
- Test: `scripts/tests/test_pack_evidence.py`

**Step 1: 对齐到最新主线**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git pull --ff-only origin main
git status -sb
```

Expected: 工作区干净，且与 `origin/main` 对齐。

**Step 2: 最小回归（防脚本链路断）**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_pack_evidence.py
```

Expected: PASS。

**Step 3: 核验关键输入存在（避免跑到一半才发现缺文件）**

Run:
```bash
cd /root/projects/4d-recon
ls -la outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz
ls -la outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz
ls -la outputs/cue_mining/selfcap_bar_8cam60f_zeros_control/pseudo_masks.npz
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200/stats/test_step0199.json
```

Expected: 全部存在。

---

### Task 2: Smoke200 Run #1（控制组，Plan-B init + zeros mask）

**Files:**
- Create: (none)
- Modify: (none)
- Test: (none)

**Step 1: 运行训练（200 steps）**

Run:
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py

DATA_DIR=data/selfcap_bar_8cam60f
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz
MASK_NPZ=outputs/cue_mining/selfcap_bar_8cam60f_zeros_control/pseudo_masks.npz
OUT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200

mkdir -p "$OUT"
CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 200 \
  --eval-steps 200 \
  --save-steps 200 \
  --seed 42 \
  --train-camera-names 02,03,04,05,06,07 \
  --val-camera-names 08 \
  --test-camera-names 09 \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --pseudo-mask-npz "$MASK_NPZ" \
  --pseudo-mask-weight 0.5 \
  --pseudo-mask-end-step 600 \
  --eval-on-test

python3 scripts/write_throughput_json.py "$OUT"
```

Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200/stats/test_step0199.json` 存在
- `.../stats/throughput.json` 存在

**Stoploss（立即停）**
- 若出现 NaN/训练崩溃：停止并在后续 notes 里记录报错，不做后续 run（先修）。

---

### Task 3: Smoke200 Run #2（Ours-Weak，Plan-B init + diff mask）

**Files:**
- Create: (none)
- Modify: (none)
- Test: (none)

**Step 1: 运行训练（200 steps，超参对齐现有 ours_weak_600：w=0.3,end=200）**

Run:
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py

DATA_DIR=data/selfcap_bar_8cam60f
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz
MASK_NPZ=outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz
OUT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200

mkdir -p "$OUT"
CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$OUT" \
  --start-frame 0 \
  --end-frame 60 \
  --max-steps 200 \
  --eval-steps 200 \
  --save-steps 200 \
  --seed 42 \
  --train-camera-names 02,03,04,05,06,07 \
  --val-camera-names 08 \
  --test-camera-names 09 \
  --eval-sample-every 1 \
  --eval-sample-every-test 1 \
  --render-traj-path fixed \
  --global-scale 6 \
  --pseudo-mask-npz "$MASK_NPZ" \
  --pseudo-mask-weight 0.3 \
  --pseudo-mask-end-step 200 \
  --eval-on-test

python3 scripts/write_throughput_json.py "$OUT"
```

Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200/stats/test_step0199.json` 存在
- `.../stats/throughput.json` 存在

**Stoploss（立即停）**
- 若该 run 的 `tLPIPS` 比 `planb_init_smoke200` 高出 >= 0.01（灾难性退化），停止后续 sweep，并在 notes 里给出 No‑Go 结论（cue under Plan‑B 仍负增益）。

---

### Task 4: 统一报表刷新 + smoke200 对比分析（No-GPU）

**Files:**
- Create: (none)
- Modify: (none)
- Test: (none)

**Step 1: 刷新 metrics.csv（不入库，仅用于本地核对）**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

Expected: `outputs/report_pack/metrics.csv` 包含三条 smoke200：
- `planb_init_smoke200`
- `planb_control_weak_nocue_smoke200`
- `planb_ours_weak_smoke200_w0.3_end200`

**Step 2: 生成对比表（baseline 选 planb_init_smoke200）**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md outputs/report_pack/scoreboard_smoke200_planb_plus_weak.md \
  --select_prefix outputs/protocol_v1/ \
  --select_contains selfcap_bar_8cam60f \
  --baseline_regex '^planb_init_smoke200$' \
  --step 199 \
  --stage test
```

Expected: `outputs/report_pack/scoreboard_smoke200_planb_plus_weak.md` 生成，包含 ΔPSNR/ΔLPIPS/ΔtLPIPS。

---

### Task 5: 结论沉淀 + 交接（入库）

**Files:**
- Create: `notes/planb_plus_weak_smoke200_owner_a.md`
- Create: `notes/handoff_planb_plus_weak_smoke200_owner_a.md`
- Modify: `Progress.md`（可选，一行状态更新）

**Step 1: 写结论 notes（必须可直接贴到写作/答辩）**

Create `notes/planb_plus_weak_smoke200_owner_a.md`，必须包含：
- 三条 run 的路径（含 `stats/test_step0199.json`）
- 一个 3 行表（PSNR/LPIPS/tLPIPS）
- 相对 `planb_init_smoke200` 的 ΔPSNR/ΔLPIPS/ΔtLPIPS
- 一句话结论（Go/No‑Go）：是否值得为 “Plan‑B + weak cue” 申请新决议扩 1 次 full600（必须写触发条件）

**Step 2: 写 handoff（给 B 刷 v22/v23 pack 用）**

Create `notes/handoff_planb_plus_weak_smoke200_owner_a.md`，必须包含：
- 结果目录：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200`
  - `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200`
- 本地对比表路径（不入库，但可复现生成）：
  - `outputs/report_pack/scoreboard_smoke200_planb_plus_weak.md`
- 复现命令（只需列 Task 2/3 的两条命令即可）

**Step 3:（可选）更新 Progress.md**

若结论明确（Go 或 No‑Go），在 `Progress.md` 的“一句话”或“当前待办”处追加 1 行。

**Step 4: Commit + Push（只提交 notes/docs）**

Run:
```bash
cd /root/projects/4d-recon
git status -sb
git add notes/planb_plus_weak_smoke200_owner_a.md notes/handoff_planb_plus_weak_smoke200_owner_a.md Progress.md
git commit -m "docs(planb): add planb+weak smoke200 synergy verdict (owner-a)"
git push origin HEAD:main
```

