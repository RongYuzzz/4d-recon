# OpenProposal — Pre‑Expert Weight Tune (weak `staticp99`) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在“不请专家”前，用**最省事**的方式验证：把 weak `staticp99` 的 `pseudo_mask_weight` 从 `0.8 → 0.7`，能否让 `psnr_fg↑ & lpips_fg↓` 在 **2 个 seed** 下稳定成立（并满足 `ΔtLPIPS<=+0.01`）。

**Architecture:** 复用已存在的 seed43/44 baseline（不重跑 baseline），只新增 **2 个 treatment 600-step run**（seed43/44 各 1），再用统一口径 masked eval 产出 `Δpsnr_fg/Δlpips_fg/ΔtLPIPS`。若两 seed 都过 gate，则可认为“稳定性显著改善”；否则立即止损（不做参数扫描）。

**Tech Stack:** Bash, Python, pytest, FreeTimeGsVanilla venv (`third_party/FreeTimeGsVanilla/.venv`), THUman4.0 s00 adapter outputs, `scripts/run_train_planb_init_selfcap.sh`, `scripts/eval_masked_metrics.py`.

---

## Preconditions / Non‑goals

- **local-eval only**：禁止把 `data/`、`outputs/` 加入 git；只提交 `notes/`（可选）与本计划文档。
- `outputs/` **append-only**：禁止覆盖旧目录；如重跑，使用新目录名或先 rename 旧目录。
- 公平性 gate：treatment 必须与同 seed baseline 使用同一 `init_npz_path`。
- 本计划只做一个最小调整：`pseudo_mask_weight=0.7`（其余保持与 seedrep 相同）。

## Locked inputs (must exist)

```bash
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"
MASK_NPZ="$REPO_ROOT/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz"
PLANB_INIT_NPZ="$REPO_ROOT/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz"

test -x "$VENV_PYTHON"
test -d "$DATA_DIR/images"
test -d "$DATA_DIR/masks"
test -d "$DATA_DIR/triangulation"
test -f "$MASK_NPZ"
test -f "$PLANB_INIT_NPZ"
```

Expected: all `test -...` pass.

---

### Task 0 — Create Worktree + Gate Checks

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

**Step 1: Create an isolated worktree (same code version as seedrep)**

> seedrep 的 code hash 记录在 `notes/openproposal_preexpert_seedrep_staticp99.md`。

Run:
```bash
git worktree add -b owner-b-20260305-preexpert-weight-tune-staticp99 \
  .worktrees/owner-b-20260305-preexpert-weight-tune-staticp99 \
  e0e9fa55f57842762d2630dca8c99bd487126dd1
cd .worktrees/owner-b-20260305-preexpert-weight-tune-staticp99
```

Expected: `git status` clean.

**Step 2: Sanity tests**

Run: `pytest -q`  
Expected: PASS

**Step 3: Verify baseline anchors exist (do not rerun baselines)**

Run:
```bash
set -euo pipefail
REPO_ROOT="$(pwd)"
BASE="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f"

test -f "$BASE/_seedrep_planb_init_600_seed43/stats/test_step0599.json"
test -f "$BASE/_seedrep_planb_init_600_seed43/stats_masked/test_step0599.json"
test -f "$BASE/_seedrep_planb_init_600_seed44/stats/test_step0599.json"
test -f "$BASE/_seedrep_planb_init_600_seed44/stats_masked/test_step0599.json"
```

Expected: all four files exist.

---

### Task 1 — Define Run Matrix (2 new treatments only)

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

Seeds:
- `SEED_A=43`
- `SEED_B=44`

Baseline dirs (reuse):
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed43`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed44`

New treatment dirs (append-only):
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed43`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed44`

---

### Task 2 — Run Treatment (seed43, `w=0.7`, 600 steps)

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

Run:
```bash
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"
PLANB_INIT_NPZ="$REPO_ROOT/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz"
MASK_NPZ="$REPO_ROOT/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz"

GPU="${GPU:-0}"
MAX_STEPS=600
SEED=43
RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed43"

EXTRA_TRAIN_ARGS="--pseudo-mask-npz $MASK_NPZ --pseudo-mask-weight 0.7 --pseudo-mask-end-step 600"

DATA_DIR="$DATA_DIR" GPU="$GPU" MAX_STEPS="$MAX_STEPS" SEED="$SEED" \
VENV_PYTHON="$VENV_PYTHON" PLANB_INIT_NPZ="$PLANB_INIT_NPZ" EXTRA_TRAIN_ARGS="$EXTRA_TRAIN_ARGS" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

Expected:
- `"$RESULT_DIR/stats/test_step0599.json"` exists
- `"$RESULT_DIR/cfg.yml"` contains `seed: 43`, `pseudo_mask_weight: 0.7`, `pseudo_mask_end_step: 600`
- `init_npz_path` equals `outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`

Hard check:
```bash
rg -n "^seed:|^init_npz_path:|^pseudo_mask_npz:|^pseudo_mask_weight:|^pseudo_mask_end_step:" "$RESULT_DIR/cfg.yml"
```

---

### Task 3 — Run Treatment (seed44, `w=0.7`, 600 steps)

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

Run (建议用另一张 GPU 并行；否则等 Task 2 完成后复用 GPU=0 即可):
```bash
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"
PLANB_INIT_NPZ="$REPO_ROOT/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz"
MASK_NPZ="$REPO_ROOT/outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz"

GPU="${GPU:-1}"
MAX_STEPS=600
SEED=44
RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed44"

EXTRA_TRAIN_ARGS="--pseudo-mask-npz $MASK_NPZ --pseudo-mask-weight 0.7 --pseudo-mask-end-step 600"

DATA_DIR="$DATA_DIR" GPU="$GPU" MAX_STEPS="$MAX_STEPS" SEED="$SEED" \
VENV_PYTHON="$VENV_PYTHON" PLANB_INIT_NPZ="$PLANB_INIT_NPZ" EXTRA_TRAIN_ARGS="$EXTRA_TRAIN_ARGS" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

Expected:
- `"$RESULT_DIR/stats/test_step0599.json"` exists
- `"$RESULT_DIR/cfg.yml"` contains `seed: 44`, `pseudo_mask_weight: 0.7`, `pseudo_mask_end_step: 600`
- same `init_npz_path` as baseline

Hard check:
```bash
rg -n "^seed:|^init_npz_path:|^pseudo_mask_npz:|^pseudo_mask_weight:|^pseudo_mask_end_step:" "$RESULT_DIR/cfg.yml"
```

---

### Task 4 — Masked Eval for the 2 New Treatments (foreground ROI)

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

For each new `RESULT_DIR`, run:
```bash
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"

RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.7_600_seed43"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir "$DATA_DIR" \
  --result_dir "$RESULT_DIR" \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --mask_thr 0.5 \
  --lpips_backend auto
```

Expected: `"$RESULT_DIR/stats_masked/test_step0599.json"` exists for both seeds.

---

### Task 5 — Decision Gate (2 seeds)

**Files:**
- Create: *(none)*
- Modify: *(none)*
- Test: *(none)*

Run:
```bash
python3 - <<'PY'
import json
from pathlib import Path

REPO = Path(".").resolve()
BASE = REPO / "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f"

pairs = [
    ("seed43",
     BASE / "_seedrep_planb_init_600_seed43",
     BASE / "_seedrep_weak_staticp99_w0.7_600_seed43"),
    ("seed44",
     BASE / "_seedrep_planb_init_600_seed44",
     BASE / "_seedrep_weak_staticp99_w0.7_600_seed44"),
]

def load(p: Path, rel: str):
    return json.loads((p / rel).read_text(encoding="utf-8"))

ok_all = True
for tag, bdir, tdir in pairs:
    b_full = load(bdir, "stats/test_step0599.json")
    t_full = load(tdir, "stats/test_step0599.json")
    b_fg = load(bdir, "stats_masked/test_step0599.json")
    t_fg = load(tdir, "stats_masked/test_step0599.json")

    d_psnr_fg = float(t_fg["psnr_fg"]) - float(b_fg["psnr_fg"])
    d_lpips_fg = float(t_fg["lpips_fg"]) - float(b_fg["lpips_fg"])
    d_tlpips = float(t_full["tlpips"]) - float(b_full["tlpips"])

    pass_fg = (d_psnr_fg > 0.0) and (d_lpips_fg < 0.0)
    pass_guard = (d_tlpips <= 0.01)
    ok = pass_fg and pass_guard
    ok_all = ok_all and ok

    print("===", tag)
    print("baseline", bdir.name)
    print("treat   ", tdir.name)
    print(f"Δpsnr_fg  {d_psnr_fg:+.6f}")
    print(f"Δlpips_fg {d_lpips_fg:+.6f}")
    print(f"ΔtLPIPS   {d_tlpips:+.6f}  (guardrail <= +0.01)  pass={pass_guard}")
    print("pass_fg", pass_fg, "pass_guard", pass_guard, "OK", ok)
    print()

print("OVERALL_OK", ok_all)
PY
```

Decision:
- If `OVERALL_OK=True`: 认为“稳定性显著改善”，可以先不请专家；如需更硬结论，追加一个 seed（45）做确认即可。
- If `OVERALL_OK=False`: 立即止损（不做进一步 weight 扫描），转入专家诊断或更换假设。

---

### Task 6 — Write Audit Note (append-only)

**Files:**
- Create: `notes/openproposal_preexpert_weight_tune_staticp99.md`
- Modify: *(none)*
- Test: *(none)*

Create note and include:
- 复用的 baseline dirs（seed43/44）
- 两个新 treatment dirs（seed43/44, `w=0.7`）
- `MASK_NPZ` / `PLANB_INIT_NPZ` 路径（建议写 sha256）
- 逐 seed `Δpsnr_fg / Δlpips_fg / ΔtLPIPS` 与 `OVERALL_OK`
- 最终决策（继续/止损/请专家）

Optional commit:
```bash
git add notes/openproposal_preexpert_weight_tune_staticp99.md
git commit -m "docs(notes): pre-expert weight tune for weak staticp99"
```

