# Plan-B Slice Template Hygiene (seg400_460 + seg1800_1860) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 **不新增 full600** 的前提下（仅 smoke200，GPU0），把 `seg400_460` 与 `seg1800_1860` 的 Plan‑B slice 证据改成“**仅替换 velocities**”的严格口径：使用该 slice 自己的 baseline init（positions/colors/times/durations）作为模板重新生成 Plan‑B init，并重跑对应 `planb_init_smoke200`，确保 anti‑cherrypick 证据位不被“模板来自 canonical”质疑。

**Architecture:** 对每个 slice：
1) 生成/固化该 slice 的 baseline init 模板 `outputs/plan_b/<slice>/_baseline_init/keyframes_60frames_step5.npz`；
2) 用该模板运行 `scripts/init_velocity_from_points.py` 覆盖生成 `outputs/plan_b/<slice>/init_points_planb_step5.npz`；
3) 仅重跑该 slice 的 `planb_init_smoke200`（不重跑 baseline）；
4) 更新 `notes/`（Gate/anti-cherrypick/handoff）与 `Progress.md`，供 Owner B 刷新 v25 report-pack/evidence。

**Tech Stack:** `third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py`、`scripts/init_velocity_from_points.py`、`scripts/run_train_planb_init_selfcap.sh`、`scripts/tests/test_*.py`。

---

## 硬约束（违反即不可比）

1. 仅 `GPU=0`，仅 `MAX_STEPS=200`；禁止任何新增 full600。
2. 不改 `docs/protocols/protocol_v1.yaml`；不改 canonical `data/selfcap_bar_8cam60f` 口径。
3. 不提交 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只提交 `notes/`、`Progress.md`（必要时可提交一个新 `docs/plans/*.md` 追加说明，但默认不需要）。
4. 若 re-template 后 slice 方向反转：**不追加任何额外跑数**，直接记录为“slice 限制/不纳入防守位”并交给 Owner B 写作处理。

---

## Task A111: 建立干净执行环境（worktree + 预检）

**Files**
- Create: `notes/planb_template_hygiene_preflight_owner_a.md`

**Steps**
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-planb-template-hygiene origin/main
cd .worktrees/owner-a-20260226-planb-template-hygiene

git rev-parse HEAD
git log -n 5 --oneline

python3 scripts/tests/test_init_velocity_from_points_contract.py
python3 scripts/tests/test_pack_evidence.py
```

Expected: PASS。

在 `notes/planb_template_hygiene_preflight_owner_a.md` 记录：
- HEAD + 最近 5 条提交
- 两项测试 PASS

---

## Task A112: seg400_460 重新生成模板 + 重跑 planb_init_smoke200（GPU0）

**目标 slice**
- `DATA_DIR=data/selfcap_bar_8cam60f_seg400_460`
- `OUT_SLICE=outputs/plan_b/selfcap_bar_8cam60f_seg400_460`
- `RUN_DIR=outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200`
- baseline 对照（不重跑）：`outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200/stats/test_step0199.json`

**Step 1: 备份旧证据到 /tmp（避免覆盖后无法回滚）**
```bash
mkdir -p /tmp/planb_template_hygiene_backup/seg400_460
cp -av \
  /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg400_460/init_points_planb_step5.npz \
  /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json \
  /tmp/planb_template_hygiene_backup/seg400_460/
cp -av \
  /root/projects/4d-recon/outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/stats/test_step0199.json \
  /root/projects/4d-recon/outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/stats/throughput.json \
  /root/projects/4d-recon/outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  /tmp/planb_template_hygiene_backup/seg400_460/ || true
```

**Step 2: 固化该 slice 的 baseline init 模板**

优先复用已存在的 baseline smoke200 keyframes（更严格对齐 baseline）：
```bash
mkdir -p /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init
cp -av \
  /root/projects/4d-recon/outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200/keyframes_60frames_step5.npz \
  /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init/keyframes_60frames_step5.npz
```

**Step 3: 用 slice 模板重生成 Plan‑B init（覆盖旧 init_points_planb_step5.npz）**
```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg400_460 \
  --baseline_init_npz outputs/plan_b/selfcap_bar_8cam60f_seg400_460/_baseline_init/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg400_460
```

**Step 4: Gate‑S1 验收（No‑GPU）**
- `outputs/plan_b/selfcap_bar_8cam60f_seg400_460/velocity_stats.json` 存在
- `counts.match_ratio_over_eligible >= 0.05`
- `clip_threshold_m_per_frame` 不超过 canonical 的 `10x`

**Step 5: 重跑 planb_init_smoke200（GPU0，覆盖原 RUN_DIR）**
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-template-hygiene
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg400_460 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg400_460/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

**Step 6: Gate‑S2 验收**
- `RUN_DIR/stats/test_step0199.json` 存在
- 读取 baseline vs planb 的 PSNR/LPIPS/tLPIPS 与差值
- PASS 条件（满足任一条）：
  - tLPIPS 相对 baseline 下降 ≥ 5% 且 PSNR 不劣化超过 0.2 dB
  - 或 LPIPS 下降 ≥ 0.01 且训练稳定（无 NaN/发散）

---

## Task A113: seg1800_1860 重新生成模板 + 重跑 planb_init_smoke200（GPU0）

**目标 slice**
- `DATA_DIR=data/selfcap_bar_8cam60f_seg1800_1860`
- `OUT_SLICE=outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860`
- `RUN_DIR=outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200`
- baseline 对照（不重跑）：`outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/baseline_smoke200/stats/test_step0199.json`

**Step 1: 备份旧证据到 /tmp**
```bash
mkdir -p /tmp/planb_template_hygiene_backup/seg1800_1860
cp -av \
  /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/init_points_planb_step5.npz \
  /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/velocity_stats.json \
  /tmp/planb_template_hygiene_backup/seg1800_1860/
cp -av \
  /root/projects/4d-recon/outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/stats/test_step0199.json \
  /root/projects/4d-recon/outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/stats/throughput.json \
  /root/projects/4d-recon/outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  /tmp/planb_template_hygiene_backup/seg1800_1860/ || true
```

**Step 2: 生成该 slice 的 baseline init 模板（combine_frames）**
```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

mkdir -p /root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/_baseline_init
$PY third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py \
  --input-dir data/selfcap_bar_8cam60f_seg1800_1860/triangulation \
  --output-path outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/_baseline_init/keyframes_60frames_step5.npz \
  --frame-start 0 \
  --frame-end 59 \
  --keyframe-step 5
```

**Step 3: 用 slice 模板重生成 Plan‑B init（覆盖旧 init_points_planb_step5.npz）**
```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f_seg1800_1860 \
  --baseline_init_npz outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/_baseline_init/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860
```

**Step 4: Gate‑S1 验收（同 A112）**

**Step 5: 重跑 planb_init_smoke200（GPU0，覆盖原 RUN_DIR）**
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-template-hygiene
GPU=0 MAX_STEPS=200 \
DATA_DIR=data/selfcap_bar_8cam60f_seg1800_1860 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f_seg1800_1860/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1_seg1800_1860/selfcap_bar_8cam60f_seg1800_1860/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

**Step 6: Gate‑S2 验收（同 A112）**

---

## Task A114: 文档更新与交接（不改 B 的写作，只提供可引用事实）

**Files**
- Modify: `notes/planb_seg400_460_gate_s1_owner_a.md`
- Modify: `notes/planb_seg400_460_gate_s2_owner_a.md`
- Modify: `notes/anti_cherrypick_seg400_460.md`
- Modify: `notes/handoff_planb_seg400_460_owner_a.md`
- Modify: `notes/planb_seg1800_1860_gate_s1_owner_a.md`
- Modify: `notes/planb_seg1800_1860_gate_s2_owner_a.md`
- Modify: `notes/anti_cherrypick_seg1800_1860.md`
- Modify: `notes/handoff_planb_seg1800_1860_owner_a.md`
- Modify: `Progress.md`

**要求**
- 每个文件追加一个 `## Update (re-template baseline init, 2026-02-26)` 小节：
  - 写清：baseline template 路径（`outputs/plan_b/<slice>/_baseline_init/keyframes_60frames_step5.npz`）
  - 写清：Gate‑S1 关键字段（match_ratio/clip_threshold/n_clipped）
  - 写清：新的 smoke200 指标与差值（PSNR/LPIPS/tLPIPS）
  - 给出 PASS/FAIL 与一句话结论
- `Progress.md` 把 seg400_460/seg1800_1860 的条目更新为“re-template 后的最新数值”，并注明已做 template hygiene。

---

## Task A115: 回归 + 提交 + 推送（仅 docs/notes）

**Steps**
1) 全量回归：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260226-planb-template-hygiene
for t in scripts/tests/test_*.py; do python3 "$t"; done
```

2) 提交（只提交 notes/Progress）：
```bash
git add notes/planb_template_hygiene_preflight_owner_a.md \
  notes/planb_seg400_460_gate_s1_owner_a.md \
  notes/planb_seg400_460_gate_s2_owner_a.md \
  notes/anti_cherrypick_seg400_460.md \
  notes/handoff_planb_seg400_460_owner_a.md \
  notes/planb_seg1800_1860_gate_s1_owner_a.md \
  notes/planb_seg1800_1860_gate_s2_owner_a.md \
  notes/anti_cherrypick_seg1800_1860.md \
  notes/handoff_planb_seg1800_1860_owner_a.md \
  Progress.md
git commit -m "docs(planb): re-template seg400/seg1800 smoke200 to isolate velocity init"
git push origin HEAD:main
```

