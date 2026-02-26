# Plan‑B（3D Velocity Init）48h Gate 执行 + seg2 防守补齐 Implementation Plan（Owner A）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在仅使用 GPU0 的约束下，按 02‑26 决议执行 Plan‑B（triangulation→3D velocity init）**48h timebox**：完成 Gate‑B1（smoke200）与 Gate‑B2（仅 1 次 full600）并给出可审计的 Go/No‑Go；同时补齐 seg200_260 的 **control_weak_nocue_600**（anti‑cherrypick 防守证据位）。

**Architecture:** 不改 `protocol_v1` / 不改 `data/`；用 `outputs/protocol_v1/.../baseline_600/keyframes_*.npz` 作为模板（positions/colors/times/durations），用 `scripts/init_velocity_from_points.py` 仅替换 velocities（输出到 `outputs/plan_b/...`），再用 `scripts/run_train_planb_init_selfcap.sh` 只改变 init 进行训练。所有 full600 严格遵守预算与止损线。

**Tech Stack:** FreeTimeGsVanilla trainer（`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`）、Plan‑B 脚本（`scripts/init_velocity_from_points.py`）、Bash runners（`scripts/run_train_*.sh`）、report-pack（`scripts/build_report_pack.py`/`scripts/summarize_scoreboard.py`/`scripts/pack_evidence.py`）。

---

## 前置硬约束（违反即不可比/违反即超预算）

1. 决议真源（必须遵守）：
   - `docs/decisions/2026-02-26-planb-pivot.md`
   - `docs/execution/2026-02-26-planb.md`
2. 协议锁死：`docs/protocol.yaml`（-> `docs/protocols/protocol_v1.yaml`），canonical `data/selfcap_bar_8cam60f`（frames `[0,60)`，cams `02-09`）。
3. **full600 预算（7 天写死 N=3）**：
   - 本计划最多消耗 full600：`planb_init_600`（1 次） + `seg200_260_control_weak_nocue_600`（1 次）
   - `seg200_260_baseline_600` 已存在则**不重跑**（先验收产物是否齐全）
4. 不入库大文件：不提交 `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz`；只提交 `docs/*`、`notes/*` 与 `artifacts/report_packs/SHA256SUMS.txt`（如需）。
5. 叙事纪律：禁止用“零速陷阱/零速已证实”；统一口径为“velocity prior 的质量/尺度/一致性不足或噪声过大”（见决议）。

---

### Task 1: 建立干净执行环境（对齐 main + 预检）

**Files:**
- Create: `notes/planb_preflight_owner_a.md`

**Step 1: 新建干净 worktree（避免复用旧冲突目录）**

Run：
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-a-20260226-planb origin/main
cd .worktrees/owner-a-20260226-planb
```

**Step 2: 记录 provenance（写入 notes）**

Run：
```bash
git rev-parse HEAD
git log -n 5 --oneline
```

Expected：HEAD 位于包含 `docs/decisions/2026-02-26-planb-pivot.md` 的版本之后。

**Step 3: 最小健康检查（不跑 GPU）**

Run：
```bash
python3 scripts/tests/test_init_velocity_from_points_contract.py
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected：全部 PASS。

**Step 4: 数据/基线 init 预检（避免跑到一半缺文件）**

Run：
```bash
test -d data/selfcap_bar_8cam60f/triangulation
test -f outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz
test -f outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/stats/test_step0599.json
```

Expected：均返回 0。

---

### Task 2: Gate‑B1（Day1）：生成 Plan‑B init + smoke200 sanity（baseline vs planb）

**Files:**
- Create: `notes/planb_gate_b1_owner_a.md`

**Step 1: 生成 Plan‑B init（输出隔离 + 自检落盘）**

Run（必须使用 venv python，确保 scipy 可用）：
```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/init_velocity_from_points.py \
  --data_dir data/selfcap_bar_8cam60f \
  --baseline_init_npz outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz \
  --frame_start 0 \
  --frame_end_exclusive 60 \
  --keyframe_step 5 \
  --out_dir outputs/plan_b/selfcap_bar_8cam60f
```

Expected：
- `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz` 存在
- `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json` 存在
- stdout 打印 match ratio 与 v 的统计（用于 notes 记录）

**Step 2: smoke200 baseline（对照真值，命名必须以 baseline_smoke200 开头）**

Run（GPU0）：
```bash
GPU=0 MAX_STEPS=200 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window \
bash scripts/run_train_baseline_selfcap.sh
```

Expected：生成
- `.../stats/test_step0199.json`
- `.../videos/traj_4d_step199.mp4`
- `.../stats/throughput.json`

**Step 3: smoke200 planb_init（只变 init）**

Run（GPU0）：
```bash
GPU=0 MAX_STEPS=200 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200 \
bash scripts/run_train_planb_init_selfcap.sh
```

Expected：生成
- `.../stats/test_step0199.json`
- `.../videos/traj_4d_step199.mp4`
- `.../stats/throughput.json`

**Step 4: 生成 smoke200 对比表（不耗 GPU，用于 Gate‑B1 快速判断）**

Run：
```bash
python3 scripts/build_report_pack.py
python3 scripts/analyze_smoke200_m1.py --baseline_regex '^baseline_smoke200_planb_window$'
```

Expected：
- `outputs/report_pack/scoreboard_smoke200.md` 已更新且包含 `planb_init_smoke200`

**Gate‑B1 直接 No‑Go 条件（任一触发即停止 Gate‑B2）**

1. 训练不稳定：loss 爆/渲染发散/明显 NaN
2. `velocity_stats.json` 显示匹配率极低（例如 `match_ratio_over_eligible < 0.01`）或几乎全为零速度（`ratio(||v||<1e-4)` 约等于 1.0）
3. smoke200 指标与视频明显更差（尤其 test cam 画面崩）

备注（允许的“最小救火动作”）：
- 只允许调整 Plan‑B 脚本参数重新生成 init（不改协议、不改数据）：如 `--max_match_distance`、`--no_mutual_nn`、`--disable_drift_removal`、`--clip_quantile`。
- 每次调整必须在 `notes/planb_gate_b1_owner_a.md` 记录参数与 `velocity_stats.json` 路径。

---

### Task 3: Gate‑B2（Day2）：仅 1 次 full600（planb_init_600）并给 Go/No‑Go

**Files:**
- Create: `notes/planb_gate_b2_owner_a.md`

**Step 1: 跑 full600（严格只 1 次）**

Run（GPU0）：
```bash
GPU=0 MAX_STEPS=600 \
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600 \
bash scripts/run_train_planb_init_selfcap.sh
```

Expected：生成
- `.../stats/test_step0599.json`
- `.../videos/traj_4d_step599.mp4`
- `.../stats/throughput.json`

**Step 2: 快速对比 baseline_600（用于 48h 决议口径）**

Run：
```bash
python3 scripts/build_report_pack.py
python3 scripts/summarize_scoreboard.py
```

Expected：`outputs/report_pack/metrics.csv` 与 `outputs/report_pack/scoreboard.md` 包含 `planb_init_600` 条目（step=599,test）。

**Step 3: 写入 Gate‑B2 Go/No‑Go 结论（按决议口径）**

在 `notes/planb_gate_b2_owner_a.md` 中写死：
- `planb_init_600` 的 PSNR/LPIPS/tLPIPS（test@599）
- 相对 `baseline_600` 的差值
- Go/No‑Go 判定：
  - Go：`tLPIPS -5%`（vs baseline_600）且 `PSNR` 不劣化 >0.2dB，或动态 ghosting 明显减少且训练稳定
  - No‑Go：PSNR/LPIPS/tLPIPS 三项全劣化或训练不稳

---

### Task 4: Day3 防守补齐：seg200_260 的 control_weak_nocue_600（full600）

**Files:**
- Optional Modify (if you own this update): `notes/anti_cherrypick_seg200_260.md`
- Create: `notes/seg2_control_weak_nocue_600_owner_a.md`

**Step 1: 验收 seg2 baseline_600 已存在（避免浪费 full600 预算）**

Run：
```bash
test -f outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/stats/test_step0599.json
test -f outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/videos/traj_4d_step599.mp4
```

Expected：均存在则视为 “seg2 baseline_600 防守项已满足”，不重跑。

**Step 2: 跑 seg2 control_weak_nocue_600**

Run（GPU0）：
```bash
GPU=0 MAX_STEPS=600 \
DATA_DIR=data/selfcap_bar_8cam60f_seg200_260 \
CUE_TAG=selfcap_bar_8cam60f_seg200_260_zeros_control \
RESULT_DIR=outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600 \
bash scripts/run_train_control_weak_nocue_selfcap.sh
```

Expected：生成
- `.../stats/test_step0599.json`
- `.../videos/traj_4d_step599.mp4`

**Step 3: 写入防守结论（供 Writing Mode 使用）**

在 `notes/seg2_control_weak_nocue_600_owner_a.md` 记录：
- seg2 baseline_600 与 seg2 control_weak_nocue_600 的 test@599 指标对比
- 一句话结论：control 现象在 seg2 是否一致（至少趋势说明）

---

### Task 5: 交接给 Owner B（不占 GPU）

**Files:**
- Create: `notes/handoff_planb_and_seg2_to_owner_b.md`

**Step 1: 列出可直接打包/写作引用的路径（必须准确）**

至少包含：
- `outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- `outputs/plan_b/selfcap_bar_8cam60f/velocity_stats.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_smoke200_planb_window`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_smoke200`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600`
- `outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/control_weak_nocue_600`

**Step 2: 明确本轮 full600 预算消耗情况**

写明：
- 本轮新增 full600：`planb_init_600`（1 次）、`seg2_control_weak_nocue_600`（1 次）
- 未来 7 天 full600 预算剩余（按决议 N=3 计）

