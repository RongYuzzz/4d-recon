# Plan-B seg1800_1860 Smoke200 Evidence (Owner A) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 **不新增 full600** 的前提下，仅用 `GPU=0` 为 Plan‑B 增加一个“更远切片（seg1800_1860）”的 **smoke200** anti‑cherrypick 证据位，并形成可审计 `notes/` 交接材料，供 Writing Mode（Owner B）刷新后续 report-pack/evidence。

**Architecture:** 复用 `bar-release.tar.gz`，用 `scripts/adapt_selfcap_release_to_freetime.py` 生成 `data/selfcap_bar_8cam60f_seg1800_1860`；再用 `scripts/run_train_baseline_selfcap.sh` 与 `scripts/run_train_planb_init_selfcap.sh` 各跑一次 `MAX_STEPS=200`（baseline/planb），用 Gate‑S1/S2 口径验收，并在 `notes/` 落盘指标与差值。可选生成 side-by-side mp4（不入库，供 evidence 自动收录）。

**Tech Stack:** `scripts/adapt_selfcap_release_to_freetime.py`、`scripts/init_velocity_from_points.py`、`scripts/run_train_baseline_selfcap.sh`、`scripts/run_train_planb_init_selfcap.sh`、`scripts/make_side_by_side_video.sh`、FreeTimeGsVanilla venv python、`scripts/tests/test_*.py`。

---

## 硬约束（违反即不可比）

1. 不改 `docs/protocols/protocol_v1.yaml`；不改 canonical `data/selfcap_bar_8cam60f`。
2. 仅允许 smoke200（`MAX_STEPS=200`），**禁止**任何新增 full600（预算为 0）。
3. 仅使用 `GPU=0`。
4. 产物不入库：不 commit `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`。
5. 必须在 `notes/` 落盘可审计记录（命令、HEAD、指标、结论），并更新 `Progress.md`。

## 切片选择（预承诺，避免 cherry-pick）

- 本次固定切片：`frame_start=1800`、`num_frames=60`（即 seg1800_1860）。
- 原始数据覆盖范围已知为 `0..3539`（本切片不会越界），因此 **不设 fallback**。

---

### Task A101: 建立干净执行环境（worktree + 预检）

**Files:**
- Create: `notes/planb_seg1800_1860_preflight_owner_a.md`

**Step 1: 新建 worktree（从最新 origin/main）**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-planb-seg1800 origin/main
cd .worktrees/owner-a-20260226-planb-seg1800
```

**Step 2: 记录 provenance**

写入 `notes/planb_seg1800_1860_preflight_owner_a.md`：
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

### Task A102: 生成 seg1800_1860 数据切片（CPU/IO）

**Files:**
- Create: `notes/planb_seg1800_1860_data_owner_a.md`

**Step 1: 生成数据目录**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg1800_1860 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 1800 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

**Step 2: 数据契约验收**

Run:
```bash
test -d data/selfcap_bar_8cam60f_seg1800_1860/images
test -d data/selfcap_bar_8cam60f_seg1800_1860/triangulation
test -f data/selfcap_bar_8cam60f_seg1800_1860/sparse/0/cameras.bin
ls data/selfcap_bar_8cam60f_seg1800_1860/triangulation/points3d_frame*.npy | wc -l
```

Expected:
- `points3d_frame*.npy` 计数为 `60`。

将命令与验收结果写入 `notes/planb_seg1800_1860_data_owner_a.md`。

---

### Task A103: Gate‑S1（seg1800_1860 init 质量门，No‑GPU）

**Files:**
- Create: `notes/planb_seg1800_1860_gate_s1_owner_a.md`

**Step 1: 生成 Plan‑B init（仅替换 velocities）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg1800_1860 \
  --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860
```

验收（写入 `notes/planb_seg1800_1860_gate_s1_owner_a.md`）：
- `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json` 存在
- `counts.match_ratio_over_eligible >= 0.05`
- `clip_threshold_m_per_frame` 不出现相对 canonical `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json` 的 10x 以上离谱

若 FAIL：停止后续 GPU smoke200，直接进入 Task A106 handoff（记录 No‑Go 原因）。

---

### Task A104: Gate‑S2（seg1800_1860 smoke200：baseline vs planb，GPU0）

**Files:**
- Create: `notes/planb_seg1800_1860_gate_s2_owner_a.md`

**Step 1: baseline smoke200**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg1800_1860 \
RESULT_DIR=outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200 \
bash scripts/run_train_baseline_selfcap.sh
```

**Step 2: planb smoke200**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg1800_1860 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

**Step 3: Gate‑S2 判定（PASS/FAIL）**

从两个目录读取 `stats/test_step0199.json`，记录：
- PSNR / LPIPS / tLPIPS
- Δ（planb - baseline）

PASS 条件（满足任一条即可）：
1. `tLPIPS` 相对 baseline_smoke200 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
2. LPIPS 下降 ≥ 0.01 且训练稳定（无 NaN/发散）

将命令、artifact check（`stats/test_step0199.json`、`stats/throughput.json`、`videos/traj_4d_step199.mp4`）与 PASS/FAIL 写入 `notes/planb_seg1800_1860_gate_s2_owner_a.md`。

---

### Task A105 (Optional): 生成 seg1800_1860 side-by-side 定性视频（No‑GPU，本地产物）

**Files:**
- None (do not commit)

Run:
```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/videos/traj_4d_step199.mp4 \
  --right outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg1800_1860_step199.mp4 \
  --left_label baseline_seg1800_1860_smoke200 \
  --right_label planb_seg1800_1860_smoke200 \
  --overwrite
```

Expected:
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4` 存在

Note:
- 该 mp4 不入库；但后续 `scripts/pack_evidence.py` 会在存在时自动收录到 evidence tar。

---

### Task A106: 追加 anti‑cherrypick 附录记录 + handoff + 合入 main

**Files:**
- Create: `notes/anti_cherrypick_seg1800_1860.md`
- Create: `notes/handoff_planb_seg1800_1860_owner_a.md`
- Modify: `Progress.md`

**Step 1: 写 anti‑cherrypick 附录（最少内容）**
- 数据生成命令（frame_start=1800）
- Gate‑S1 关键字段
- smoke200 baseline vs planb 的指标与差值
- 一句话结论（趋势是否与 canonical/seg200_260/seg400_460/seg600_660 一致）

**Step 2: 写 handoff（必须包含路径）**
- `outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json`
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/`
- `outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/`
- `notes/anti_cherrypick_seg1800_1860.md`

**Step 3: 全量回归**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg1800
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: PASS。

**Step 4: 提交并推送（只提交 docs/notes/Progress，不提交 outputs/data）**

Run:
```bash
git add notes/planb_seg1800_1860_preflight_owner_a.md \
  notes/planb_seg1800_1860_data_owner_a.md \
  notes/planb_seg1800_1860_gate_s1_owner_a.md \
  notes/planb_seg1800_1860_gate_s2_owner_a.md \
  notes/anti_cherrypick_seg1800_1860.md \
  notes/handoff_planb_seg1800_1860_owner_a.md \
  Progress.md
git commit -m "docs(planb): add seg1800_1860 smoke200 evidence for anti-cherrypick"
git push origin HEAD:main
```

