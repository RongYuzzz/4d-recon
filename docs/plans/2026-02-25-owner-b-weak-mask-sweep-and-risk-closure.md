# Owner B Weak Mask Sweep + Risk Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改 `docs/protocol.yaml (protocol_v1)` 的前提下，用 **GPU1** 做一轮“弱融合（pseudo mask）”的**定向 sweep**，目标是：
1) 找到一个 `PSEUDO_MASK_WEIGHT / PSEUDO_MASK_END_STEP` 组合在 canonical 段（`selfcap_bar_8cam60f`）上能**稳定不差于 baseline**且尽量消除 `control_weak_nocue_600` 优于 `ours_weak_600` 的风险信号；或  
2) 若做不到，则给出**明确的止损结论**与“差异量级/噪声解释”，把风险从“红旗”降级为“已解释的限制”。

**Architecture:** 不改训练器主逻辑（避免引入不可控行为），只用现有入口脚本反复跑短/满预算实验，统一用 `scripts/build_report_pack.py` 的 `metrics.csv` 与 `scripts/summarize_scoreboard.py` 的 scoreboard 做选型，并把结论落到 `notes/weak_tuning_selfcap_bar.md`（追加一节，包含命令与指标）。

**Tech Stack:** bash、Python（现有脚本）、GPU1。

---

### Task 1: Create Owner-B Worktree (GPU1-only)

**Step 1: Create worktree**

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260225-weak-sweep .worktrees/owner-b-20260225-weak-sweep main
git -C .worktrees/owner-b-20260225-weak-sweep status --porcelain=v1
```

Expected: worktree 干净（无输出）。

---

### Task 2: Preflight Checks (No GPU)

**Step 1: Ensure canonical data exists**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep
test -d data/selfcap_bar_8cam60f/triangulation
test -d data/selfcap_bar_8cam60f/images
test -d data/selfcap_bar_8cam60f/sparse/0
```

Expected: 全部通过。

**Step 2: Ensure canonical cue exists (protocol_v1)**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep
test -f outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz
test -f outputs/cue_mining/selfcap_bar_8cam60f_v1/quality.json
```

Expected: 全部通过。

---

### Task 3: Weak Sweep v2 (GPU1, 200-step first, keep runs auditable)

**原则：**
- 不改 protocol 的 frozen 项（帧段/相机 split/seed/global_scale/keyframe_step）。
- 只调 `PSEUDO_MASK_WEIGHT` 与 `PSEUDO_MASK_END_STEP`（属于 ours_weak 的可调权重/窗口）。
- 先跑 `MAX_STEPS=200` 做筛选，再挑 1-2 个跑 `MAX_STEPS=600`。

**Step 1: Run a focused 200-step grid (建议 6 个以内)**

推荐组合（覆盖“更强权重/更短窗口/更长窗口”三个方向）：
- A: `w=0.1, end=200`
- B: `w=0.3, end=60`
- C: `w=0.3, end=200`（复核当前默认，作为 anchor）
- D: `w=0.3, end=600`
- E: `w=1.0, end=200`
- F: `w=1.0, end=600`

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep

for spec in \
  "0.1 200" \
  "0.3 60" \
  "0.3 200" \
  "0.3 600" \
  "1.0 200" \
  "1.0 600"; do
  w="$(echo "$spec" | awk '{print $1}')"
  end="$(echo "$spec" | awk '{print $2}')"
  GPU=1 MAX_STEPS=200 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
  RESULT_DIR=outputs/sweeps/weak_mask_v2/selfcap_bar_8cam60f/w${w}_end${end}_s200 \
  CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
  PSEUDO_MASK_WEIGHT="$w" PSEUDO_MASK_END_STEP="$end" \
  bash scripts/run_train_ours_weak_selfcap.sh
done
```

Expected:
- 每个目录均产出：
  - `stats/test_step0199.json`
  - `videos/traj_4d_step199.mp4`

**Step 2: Build report-pack and quickly compare**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv > outputs/report_pack/scoreboard.md
rg -n "weak_mask_v2|ours_weak_600|control_weak_nocue_600|baseline_600" outputs/report_pack/metrics.csv | head -n 80
```

Expected: `metrics.csv` 内能找到上述 sweep 的行。

**Step 3: Pick 1-2 best candidates to full600**

选型规则（按优先级）：
1. `tLPIPS` 下降趋势（越小越好）
2. `LPIPS` 不变差（或下降）
3. `PSNR` 不明显掉（容忍小幅波动）

---

### Task 4: Full600 Confirmation (GPU1, max 2 runs)

**Step 1: Run full600 for the best candidate**

Run（示例，按你选中的组合替换 w/end）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep

GPU=1 MAX_STEPS=600 EVAL_ON_TEST=1 EVAL_SAMPLE_EVERY_TEST=1 \
RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_w0.3_end600_600 \
CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
PSEUDO_MASK_WEIGHT=0.3 PSEUDO_MASK_END_STEP=600 \
bash scripts/run_train_ours_weak_selfcap.sh
```

Expected:
- `stats/test_step0599.json` 存在且含 `tlpips`
- `videos/traj_4d_step599.mp4` 存在

**Step 2 (Optional): Run a 2nd full600 if 1st is inconclusive**

约束：最多 2 次 full600；若两次均无收益趋势，直接止损进入 Task 5。

---

### Task 5: Risk Closure Write-up (No GPU, must deliver even if negative)

**Files:**
- Modify: `notes/weak_tuning_selfcap_bar.md`

**Step 1: Append a new section “Weak Mask Sweep v2（2026-02-25, GPU1）”**

内容要求（必须包含）：
- 每个候选 run 的 `RESULT_DIR` 路径
- `test@199`/`test@599`（如有） 的 PSNR/SSIM/LPIPS/tLPIPS
- 结论三选一（写死，避免答辩摇摆）：
  1. **ADOPT**：明确推荐的 v2 配置（w/end），并说明是否优于 `ours_weak_600`/`control_weak_nocue_600`
  2. **KEEP v1**：v2 没有更好，继续使用 `ours_weak_600 (w=0.3,end=200)`
  3. **STOPLOSS**：weak 的收益在 canonical 段不可稳定复现，作为限制写入 failure cases（但 seg2 仍可作为 anti-cherrypick 正例引用）

**Step 2: Ensure note is auditable**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep
rg -n "Weak Mask Sweep v2|ADOPT|KEEP v1|STOPLOSS" notes/weak_tuning_selfcap_bar.md
```

Expected: 命中新增段落。

---

### Task 6: Handoff To Owner A (for packaging)

**Step 1: Provide A the minimal paths**

发给 A 的信息（复制即可）：
- 选中的 full600 目录（或明确“无 full600，已止损”）：
  - `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_v2_.../`
- 若需要同步到主阵地：只需 `cfg.yml`、`stats/`、`videos/`、`keyframes*.npz`（不要 sync `renders/ckpts/tb`）。

---

### Task 7: Commit (notes only; do NOT commit outputs)

**Step 1: Run minimal tests**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_build_report_pack.py
```

Expected: PASS。

**Step 2: Commit note update**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-weak-sweep
git add notes/weak_tuning_selfcap_bar.md
git commit -m "notes(weak): add weak mask sweep v2 results and risk closure"
git push origin HEAD:main
```

Expected: push 成功（fast-forward）。

