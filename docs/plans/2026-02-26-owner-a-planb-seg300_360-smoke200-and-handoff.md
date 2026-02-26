# Plan-B seg300_360 Smoke200 Evidence + Handoff Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不新增任何 full600 的前提下（仅 `MAX_STEPS=200`，`GPU=0`），补齐 `seg300_360` 的 baseline vs planb smoke200 对比证据，并以 `notes/` 交付可审计 handoff，供 Writing Mode（Owner B）纳入后续 report-pack/evidence。

**Architecture:** 用 `scripts/adapt_selfcap_release_to_freetime.py` 生成 `data/selfcap_bar_8cam60f_seg300_360`；先跑 baseline_smoke200，再用该 baseline 产物生成 slice 自己的 init 模板并通过 `scripts/init_velocity_from_points.py` 只替换 velocities 生成 Plan‑B init，最后跑 planb_init_smoke200 并记录 Gate‑S1/S2 与指标差值。可选生成 side-by-side mp4（不入库）。

**Tech Stack:** `scripts/adapt_selfcap_release_to_freetime.py`、`scripts/run_train_baseline_selfcap.sh`、`scripts/run_train_planb_init_selfcap.sh`、`scripts/init_velocity_from_points.py`、`scripts/make_side_by_side_video.sh`、FreeTimeGsVanilla venv python。

**目标（Why now）**
- 为 Plan‑B anti-cherrypick 增加一个“预承诺的额外切片”证据位：`seg300_360`（smoke200）。
- 该切片已在 `scripts/summarize_planb_anticherrypick.py` 中作为 fallback 段落存在；本计划把它从“缺失兜底”补齐为“真实证据”，减少写作阶段被质疑 cherry-pick 的风险。
- 交付必须可被 Writing Mode（Owner B）直接打包到后续 report-pack/evidence 中。

**硬约束（违反即不可比）**
1. 仅 `GPU=0`；仅 `MAX_STEPS=200`（smoke200）；**禁止**新增任何 full600。
2. 不改 `docs/protocols/protocol_v1.yaml`；不改 canonical `data/selfcap_bar_8cam60f` 口径。
3. 不提交 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只提交 `notes/*` + `Progress.md`。
4. 口径要求（template hygiene）：Plan‑B init 必须以该切片的 baseline init 模板为基底（只替换 velocities）。
5. 记录必须可审计：命令、HEAD、关键路径、Gate‑S1/S2、指标差值、结论、handoff。

---

## 预承诺切片

- 固定切片：`frame_start=300`、`num_frames=60`，即 `seg300_360`。
- 不设“换切片挑结果”的 fallback（该范围应在 raw tar 覆盖内）。

---

## Task A121：建立干净执行环境（worktree + 预检）

**产出**
- 新增：`notes/planb_seg300_360_preflight_owner_a.md`

**步骤**
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-planb-seg300 origin/main
cd .worktrees/owner-a-20260226-planb-seg300

# 共享主阵地大目录（避免 worktree 下 outputs/data 空壳导致产物不可见）
test -e outputs || ln -s /root/projects/4d-recon/outputs outputs
test -e data || ln -s /root/projects/4d-recon/data data

# provenance（写入 notes/planb_seg300_360_preflight_owner_a.md）
git rev-parse HEAD
git log -n 5 --oneline

# 最小预检（不跑 GPU）
python3 scripts/tests/test_init_velocity_from_points_contract.py
python3 scripts/tests/test_pack_evidence.py
```

验收：两项测试 PASS。

---

## Task A122：生成 seg300_360 数据切片（CPU/IO）

**产出**
- 新增：`notes/planb_seg300_360_data_owner_a.md`

**步骤**
1. 可选 raw 覆盖性检查（慢可跳过，改为直接跑 adapter）：
```bash
tar -tzf /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz bar-release/pcds/000300.ply >/dev/null
tar -tzf /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz bar-release/pcds/000359.ply >/dev/null
```

2. 生成数据目录：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg300_360 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 300 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

3. 数据契约验收（写入 notes）：
```bash
test -d data/selfcap_bar_8cam60f_seg300_360/images
test -d data/selfcap_bar_8cam60f_seg300_360/triangulation
test -f data/selfcap_bar_8cam60f_seg300_360/sparse/0/cameras.bin
ls data/selfcap_bar_8cam60f_seg300_360/triangulation/points3d_frame*.npy | wc -l
```

验收：`points3d_frame*.npy` 计数为 `60`。

---

## Task A123：baseline_smoke200（GPU0）

**产物路径（不入库，但必须在主阵地可见）**
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200/`

**步骤**
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200 \
bash scripts/run_train_baseline_selfcap.sh
```

验收（最少）：
- `.../stats/test_step0199.json` 存在
- `.../stats/throughput.json` 存在
- `.../videos/traj_4d_step199.mp4` 存在

---

## Task A124：Gate‑S1（template hygiene init：仅替换 velocities，No‑GPU）

**产出**
- 新增：`notes/planb_seg300_360_gate_s1_owner_a.md`

**步骤**
1. 固化 baseline init 模板（强制使用该切片 baseline 产物作为模板，避免“模板来自 canonical”争议）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300
mkdir -p outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init
cp -av \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200/keyframes_60frames_step5.npz \
  outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init/keyframes_60frames_step5.npz
```

2. 生成 Plan‑B init（只替换 velocities + 产出 velocity_stats.json）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg300_360 \
  --baseline_init_npz outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg300_360
```

**Gate‑S1 验收（写入 notes）**
- `outputs/plan_b/selfcap_bar_8cam60f_seg300_360/velocity_stats.json` 存在
- `counts.match_ratio_over_eligible >= 0.05`（否则 No‑Go，停止后续 GPU）
- `clip_threshold_m_per_frame` 不出现相对 canonical `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json` 的 `>=10x` 异常

---

## Task A125：planb_init_smoke200（GPU0）

**产物路径（不入库，但必须在主阵地可见）**
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200/`

**步骤**
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg300_360/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

**Gate‑S2 判定（写入 notes/planb_seg300_360_gate_s2_owner_a.md）**
- 读取：
  - baseline：`.../baseline_smoke200/stats/test_step0199.json`
  - planb：`.../planb_init_smoke200/stats/test_step0199.json`
- 记录：PSNR / LPIPS / tLPIPS 与差值 Δ(planb-baseline)。
- PASS 条件（满足任一条）：
  1. `tLPIPS` 相对 baseline 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
  2. LPIPS 下降 ≥ 0.01 且训练稳定（无 NaN/发散）

---

## Task A126（可选）：生成 seg300_360 side-by-side 定性视频（No‑GPU，本地产物）

> 不入库；但后续 `scripts/pack_evidence.py` 会自动收录 `outputs/qualitative/planb_vs_baseline/*.mp4` 到 evidence tar。

```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200/videos/traj_4d_step199.mp4 \
  --right outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg300_360_step199.mp4 \
  --left_label baseline_seg300_360_smoke200 \
  --right_label planb_seg300_360_smoke200 \
  --overwrite
```

---

## Task A127：anti-cherrypick 附录 + handoff + 合入 main

**产出（入库）**
- 新增：`notes/planb_seg300_360_gate_s2_owner_a.md`
- 新增：`notes/anti_cherrypick_seg300_360.md`
- 新增：`notes/handoff_planb_seg300_360_owner_a.md`
- 更新：`Progress.md`

**anti_cherrypick_seg300_360.md 必含**
- 数据生成命令（adapter frame_start=300）
- Gate‑S1 关键字段（match_ratio/clip_threshold/n_clipped）
- smoke200 baseline vs planb 的指标与差值
- 一句话结论：是否与 canonical/seg200_260/seg400_460/seg600_660/seg1800_1860 同向；是否建议纳入 anti-cherrypick 防守位

**handoff 必含路径（给 Owner B）**
- `outputs/plan_b/selfcap_bar_8cam60f_seg300_360/velocity_stats.json`
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_smoke200/`
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_smoke200/`
- （若做了 A126）`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4`
- `notes/anti_cherrypick_seg300_360.md`

**回归（提交前）**
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg300
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

**提交与推送（只提交 notes/Progress）**
```bash
git add notes/planb_seg300_360_preflight_owner_a.md \
  notes/planb_seg300_360_data_owner_a.md \
  notes/planb_seg300_360_gate_s1_owner_a.md \
  notes/planb_seg300_360_gate_s2_owner_a.md \
  notes/anti_cherrypick_seg300_360.md \
  notes/handoff_planb_seg300_360_owner_a.md \
  Progress.md
git commit -m "docs(planb): add seg300_360 smoke200 evidence (template hygiene) for anti-cherrypick"
git push origin HEAD:main
```
