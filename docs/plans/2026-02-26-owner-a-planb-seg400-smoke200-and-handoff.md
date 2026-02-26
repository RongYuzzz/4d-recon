# Plan-B seg400_460 Smoke200 Evidence (Owner A) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 full600 预算已用尽的前提下，仅用 `GPU=0` 跑一个“第三切片（seg400_460）”的 Plan‑B smoke200，对 Plan‑B 的 anti‑cherrypick 防守再加一层证据，并把结果以 `notes/` 可审计方式交接给 Writing Mode（Owner B）。

**Architecture:** 复用现有 SelfCap `bar-release.tar.gz`，用 `scripts/adapt_selfcap_release_to_freetime.py` 生成 `data/selfcap_bar_8cam60f_seg400_460`；用 `scripts/run_train_baseline_selfcap.sh` 与 `scripts/run_train_planb_init_selfcap.sh` 分别跑 baseline/planb 的 smoke200（200 steps），并在 `notes/` 记录 Gate‑S1/S2 与指标差值。严禁新增 full600。

**Tech Stack:** `scripts/adapt_selfcap_release_to_freetime.py`、`scripts/init_velocity_from_points.py`、`scripts/run_train_baseline_selfcap.sh`、`scripts/run_train_planb_init_selfcap.sh`、FreeTimeGsVanilla venv python。

---

## 硬约束（违反即不可比）

1. 不改 `docs/protocols/protocol_v1.yaml`、不改 `data/selfcap_bar_8cam60f`（canonical 仍锁死）。
2. 本计划只允许 smoke200（`MAX_STEPS=200`），**禁止**任何新增 full600（预算已为 0）。
3. 产物不入库：不 commit `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`。
4. 必须在 `notes/` 落盘可审计记录（命令、HEAD、指标、结论）。

---

### Task A61: 建立干净执行环境（worktree + 预检）

**Files:**
- Create: `notes/planb_seg400_460_preflight_owner_a.md`

**Step 1: 新建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-planb-seg400 origin/main
cd .worktrees/owner-a-20260226-planb-seg400
```

**Step 2: 记录 provenance**

写入 `notes/planb_seg400_460_preflight_owner_a.md`：
- `git rev-parse HEAD`
- `git log -n 5 --oneline`

**Step 3: 最小健康检查（不跑 GPU）**

Run:
```bash
python3 scripts/tests/test_init_velocity_from_points_contract.py
python3 scripts/tests/test_pack_evidence.py
```

Expected: PASS。

---

### Task A62: 生成 seg400_460 数据切片（CPU/IO）

**Files:**
- Create: `notes/planb_seg400_460_data_owner_a.md`

**Step 1: 生成数据目录**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg400_460 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 400 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

**Step 2: 数据契约验收**

Run:
```bash
test -d data/selfcap_bar_8cam60f_seg400_460/images
test -d data/selfcap_bar_8cam60f_seg400_460/triangulation
test -f data/selfcap_bar_8cam60f_seg400_460/sparse/0/cameras.bin
ls data/selfcap_bar_8cam60f_seg400_460/triangulation/points3d_frame*.npy | wc -l
```

Expected:
- `points3d_frame*.npy` 计数为 `60`。

将命令与验收结果写入 `notes/planb_seg400_460_data_owner_a.md`。

---

### Task A63: Gate‑S1（seg400_460 init 质量门，No‑GPU）

**Files:**
- Create: `notes/planb_seg400_460_gate_s1_owner_a.md`

**Step 1: 生成 Plan‑B init（仅替换 velocities）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg400_460 \
  --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg400_460
```

验收：
- `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json` 存在
- `counts.match_ratio_over_eligible >= 0.05`
- `clip_threshold_m_per_frame` 不出现相对 canonical 10x 以上离谱（参考 `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`）

把关键字段（match_ratio、clip_threshold、n_clipped）与 PASS/FAIL 写入 `notes/planb_seg400_460_gate_s1_owner_a.md`。

若 FAIL：停止后续 GPU smoke200，直接进入 Task A66 交接（记录 No‑Go 原因）。

---

### Task A64: Gate‑S2（seg400_460 smoke200：baseline vs planb，GPU0）

**Files:**
- Create: `notes/planb_seg400_460_gate_s2_owner_a.md`

**Step 1: baseline smoke200**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg400_460 \
RESULT_DIR=outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200 \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 2: planb smoke200（强制使用 seg400_460 对应 baseline init 模板）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg400_460 \
BASELINE_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init/keyframes_60frames_step5.npz \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg400_460/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

**Step 3: Gate‑S2 判定（PASS/FAIL）**

从两个目录读取 `stats/test_step0199.json`，记录：
- PSNR / LPIPS / tLPIPS
- Δ（planb - baseline）

PASS 条件（满足任一条即可）：
1. `tLPIPS` 相对 baseline_smoke200 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
2. LPIPS 下降 ≥ 0.01 且训练稳定（无 NaN/发散）

将结论写入 `notes/planb_seg400_460_gate_s2_owner_a.md`。

---

### Task A65: 追加 anti‑cherrypick 附录记录（不跑 full600）

**Files:**
- Create: `notes/anti_cherrypick_seg400_460.md`

写入内容（最少）：
- 数据生成命令（frame_start=400）
- Gate‑S1 关键字段
- smoke200 baseline vs planb 的指标与差值
- 一句话结论（趋势是否与 canonical/seg200_260 一致）

---

### Task A66: Handoff + 合入 main

**Files:**
- Create: `notes/handoff_planb_seg400_460_owner_a.md`
- Modify: `Progress.md`（新增一行：seg400_460 smoke200 证据位是否同向）

**Step 1: 写 handoff**

必须包含路径（供 Owner B 刷新 report-pack v18 时引用）：
- `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json`
- `outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200/`
- `outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/`
- `notes/anti_cherrypick_seg400_460.md`

**Step 2: 回归检查**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg400
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: PASS。

**Step 3: 提交并推送（只提交 docs/notes/Progress，不提交 outputs/data）**

Run:
```bash
git add notes/planb_seg400_460_preflight_owner_a.md \
  notes/planb_seg400_460_data_owner_a.md \
  notes/planb_seg400_460_gate_s1_owner_a.md \
  notes/planb_seg400_460_gate_s2_owner_a.md \
  notes/anti_cherrypick_seg400_460.md \
  notes/handoff_planb_seg400_460_owner_a.md \
  Progress.md
git commit -m "docs(planb): add seg400_460 smoke200 evidence for anti-cherrypick"
git push origin HEAD:main
```

