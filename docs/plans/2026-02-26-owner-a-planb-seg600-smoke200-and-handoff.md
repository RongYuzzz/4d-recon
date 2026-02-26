# Plan-B seg600_660 Smoke200 Evidence (Owner A) Implementation Plan

**Goal:** 在 **不新增 full600** 的前提下，仅用 `GPU=0` 为 Plan‑B 补充一个“第四切片（seg600_660）”的 **smoke200** anti‑cherrypick 证据位，并以 `notes/` 可审计方式交接给 Writing Mode（Owner B）用于后续 report-pack/写作收口。

**Context / Why now:**
- 当前主线已 pivot 到 Plan‑B（见 `docs/decisions/2026-02-26-planb-pivot.md`）。
- 已有 anti‑cherrypick：canonical(full600) + seg200_260(full600) + seg400_460(smoke200)（见 `docs/report_pack/2026-02-26-v22/planb_anticherrypick.md`）。
- 本计划补充一个更远切片的 smoke200，用于增强“非 cherry-pick”防守；若结果反向，也要如实落盘，避免写作时被追问。

**Hard Constraints（违反即不可比）**
1. 不改 `docs/protocols/protocol_v1.yaml`；不改 canonical `data/selfcap_bar_8cam60f`。
2. 仅允许 smoke200：`MAX_STEPS=200`；禁止任何新增 full600（预算已锁死为 0）。
3. 仅使用 `GPU=0`。
4. 不提交 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只提交 `docs/notes/Progress.md`。
5. 记录必须可审计：命令、HEAD、关键路径、指标差值、Go/No-Go（针对“是否纳入 anti-cherrypick 防守位”）。

---

## 选择切片（seg600_660）

- 目标切片：`frame_start=600`、`num_frames=60`，数据目录：`data/selfcap_bar_8cam60f_seg600_660`。
- 若发现 raw tar 中不存在 `pcds/000600.ply` 或 `pcds/000659.ply`（越界），**fallback** 到 `seg300_360`（`frame_start=300`）。
  - 注意：fallback 只允许一次，避免变成“挑结果”。

---

## Task A91: 建立干净执行环境（worktree + 预检）

**Files**
- Create: `notes/planb_seg600_660_preflight_owner_a.md`

**Steps**
1. 新建 worktree（从最新 `origin/main`）：
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-planb-seg600 origin/main
cd .worktrees/owner-a-20260226-planb-seg600
```

2. 记录 provenance（写入 `notes/planb_seg600_660_preflight_owner_a.md`）：
```bash
git rev-parse HEAD
git log -n 5 --oneline
```

3. 最小健康检查（不跑 GPU）：
```bash
python3 scripts/tests/test_init_velocity_from_points_contract.py
python3 scripts/tests/test_pack_evidence.py
```

Expected: PASS。

---

## Task A92: 生成 seg600_660 数据切片（CPU/IO）

**Files**
- Create: `notes/planb_seg600_660_data_owner_a.md`

**Steps**
1. 预检查 raw tar 是否覆盖该范围（若太慢可跳过，改为直接跑 adapter 并观察报错）：
```bash
tar -tzf /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz bar-release/pcds/000600.ply >/dev/null
tar -tzf /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz bar-release/pcds/000659.ply >/dev/null
```

2. 生成数据目录（如越界则按“选择切片” fallback 到 `frame_start=300` 重新执行一次）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f_seg600_660 \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 600 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

3. 数据契约验收（写入 `notes/planb_seg600_660_data_owner_a.md`）：
```bash
test -d data/selfcap_bar_8cam60f_seg600_660/images
test -d data/selfcap_bar_8cam60f_seg600_660/triangulation
test -f data/selfcap_bar_8cam60f_seg600_660/sparse/0/cameras.bin
ls data/selfcap_bar_8cam60f_seg600_660/triangulation/points3d_frame*.npy | wc -l
```

Expected: `points3d_frame*.npy` 计数为 `60`。

---

## Task A93: Gate‑S1（seg600_660 init 质量门，No‑GPU）

> 目的：在跑 smoke200 前先确认 velocities 估计不离谱（匹配率、clip 阈值、near-zero 比例等）。

**Files**
- Create: `notes/planb_seg600_660_gate_s1_owner_a.md`

**Steps**
1. 生成该切片的 baseline init 模板（只做预处理，不训练）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

mkdir -p outputs/plan_b/selfcap_bar_8cam60f_seg600_660/_baseline_init
$PY third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f_seg600_660/triangulation \
  --output-path outputs/plan_b/selfcap_bar_8cam60f_seg600_660/_baseline_init/keyframes_60frames_step5.npz \
  --frame-start 0 \
  --frame-end 59 \
  --keyframe-step 5
```

2. 生成 Plan‑B init（仅替换 velocities + 输出 `velocity_stats.json`）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg600_660 \
  --baseline_init_npz outputs/plan_b/selfcap_bar_8cam60f_seg600_660/_baseline_init/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg600_660
```

3. Gate‑S1 验收（写入 `notes/planb_seg600_660_gate_s1_owner_a.md`）：
- `outputs/plan_b/selfcap_bar_8cam60f_seg600_660/velocity_stats.json` 存在
- `counts.match_ratio_over_eligible >= 0.05`（否则 No‑Go，停止后续 GPU）
- `clip_threshold_m_per_frame` 不出现相对 canonical `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json` 的 10x 以上离谱

若 FAIL：停止后续 smoke200，只写结论与 handoff（记录 FAIL 原因）。

---

## Task A94: Gate‑S2（seg600_660 smoke200：baseline vs planb，GPU0）

**Files**
- Create: `notes/planb_seg600_660_gate_s2_owner_a.md`

**Commands**
1. baseline smoke200：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg600_660 \
RESULT_DIR=outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/baseline_smoke200 \
bash scripts/run_train_baseline_selfcap.sh
```

2. planb smoke200：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg600_660 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg600_660/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

**Gate‑S2 判定（用于“是否纳入 anti-cherrypick 防守位”）**
- 从两个目录读取 `stats/test_step0199.json`，记录：PSNR / LPIPS / tLPIPS 与差值 Δ（planb - baseline）。
- PASS 条件（满足任一条即可）：
  1. `tLPIPS` 相对 baseline_smoke200 下降 ≥ 5%，且 PSNR 不劣化超过 0.2 dB
  2. LPIPS 下降 ≥ 0.01 且训练稳定（无 NaN/发散）

把命令、artifact check（`stats/test_step0199.json`、`stats/throughput.json`、`videos/traj_4d_step199.mp4`）与 PASS/FAIL 写入 `notes/planb_seg600_660_gate_s2_owner_a.md`。

---

## Task A95: anti‑cherrypick 附录 + handoff + 合入 main

**Files**
- Create: `notes/anti_cherrypick_seg600_660.md`
- Create: `notes/handoff_planb_seg600_660_owner_a.md`
- Modify: `Progress.md`

**Notes 内容要求（最少）**
1. 数据生成命令（adapter frame_start=600）
2. Gate‑S1 关键字段（match_ratio、clip_threshold、n_clipped）
3. smoke200 baseline vs planb 指标与差值
4. 一句话结论：是否与 canonical/seg200_260/seg400_460 同向

**Handoff 必须包含以下路径**
- `outputs/plan_b/selfcap_bar_8cam60f_seg600_660/velocity_stats.json`
- `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/baseline_smoke200/`
- `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/planb_init_smoke200/`
- `notes/anti_cherrypick_seg600_660.md`

**回归检查**
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-seg600
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

Expected: PASS。

**提交并推送（只提交 docs/notes/Progress）**
```bash
git add notes/planb_seg600_660_preflight_owner_a.md \
  notes/planb_seg600_660_data_owner_a.md \
  notes/planb_seg600_660_gate_s1_owner_a.md \
  notes/planb_seg600_660_gate_s2_owner_a.md \
  notes/anti_cherrypick_seg600_660.md \
  notes/handoff_planb_seg600_660_owner_a.md \
  Progress.md
git commit -m "docs(planb): add seg600_660 smoke200 evidence for anti-cherrypick"
git push origin HEAD:main
```

