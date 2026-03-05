# OpenProposal — Pre‑Expert “Cheapest Next Step” (THUman4.0 s00)

**Topic:** seed replication for the only observed `psnr_fg↑ & lpips_fg↓` setting (weak fusion, `staticp99 + w0.8`)  
**Date:** 2026-03-05  
**Scope:** local execution + local eval only (no report-pack / no evidence tar)  

> **Execution note:** 按 Task 顺序逐条执行；每个 Task 的 Expected 通过后再进入下一步。  
> **Append-only rule:** `outputs/` 不手工改旧目录；需要重跑就新建新目录（或先 rename 旧目录）。

---

## Goal (人话)

在“不请专家”前，用最小成本回答一个关键问题：

> Phase 6 里那条唯一满足 `psnr_fg↑ & lpips_fg↓` 的配置（`staticp99 + w0.8`）到底是**可复现的**，还是**偶然/不稳定**？

只要 2 个新 seed、每个 seed 跑 baseline+treatment 一对（共 4 个 600-step run），就能给出非常硬的结论。

---

## What we replicate (locked)

Anchor baseline:
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

Observed “FG win” candidate (Phase 6):
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_weak_staticp99_w0.8_600_r1`
- weak args (must match):
  - `--pseudo-mask-npz outputs/cue_mining/openproposal_thuman4_s00_diff_q0.950_ds4_med3/pseudo_masks_static_from_dyn_p99.npz`
  - `--pseudo-mask-weight 0.8`
  - `--pseudo-mask-end-step 600`

Eval convention (must match Phase 3/4):
- `scripts/eval_masked_metrics.py`
- `mask_source=dataset` (THUman dataset-provided silhouette masks)
- `bbox_margin_px=32`, `mask_thr=0.5`
- guardrail: `ΔtLPIPS <= +0.01` (treatment - baseline)

---

## Task 0 — Gate check (5–10 min)

Run:
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
test -f "$PLANB_INIT_NPZ" || echo "[WARN] PLANB_INIT_NPZ missing; runner will try to generate it"

# Optional but recommended: ensure no local code break
pytest -q
```

Expected:
- 所有 `test -d/-f` 都通过（或你接受 runner 现场生成 `PLANB_INIT_NPZ`）
- `pytest -q` 通过

---

## Task 1 — Define run matrix (2 seeds, paired A/B)

Pick two new seeds (default):
- `SEED_A=43`
- `SEED_B=44`

Define fresh result dirs (example names; you can change but keep them unambiguous):
- baseline:
  - `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed43`
  - `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed44`
- treatment:
  - `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.8_600_seed43`
  - `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.8_600_seed44`

---

## Task 2 — Run baseline for each seed (Plan‑B init, 600 steps)

Template (run twice; change `SEED` + `RESULT_DIR`):
```bash
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"
PLANB_INIT_NPZ="$REPO_ROOT/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz"

GPU="${GPU:-0}"
MAX_STEPS=600
SEED=43
RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed43"

DATA_DIR="$DATA_DIR" GPU="$GPU" MAX_STEPS="$MAX_STEPS" SEED="$SEED" \
VENV_PYTHON="$VENV_PYTHON" PLANB_INIT_NPZ="$PLANB_INIT_NPZ" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

Expected (each run):
- `"$RESULT_DIR/stats/test_step0599.json"` exists
- `"$RESULT_DIR/cfg.yml"` exists and contains the expected `init_npz_path`

Hard check (each run):
```bash
rg -n "^seed:|^init_npz_path:" "$RESULT_DIR/cfg.yml"
```

---

## Task 3 — Run treatment for each seed (same seed, same init, add weak fusion)

Template (run twice; change `SEED` + `RESULT_DIR`):
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
RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_weak_staticp99_w0.8_600_seed43"

EXTRA_TRAIN_ARGS="--pseudo-mask-npz $MASK_NPZ --pseudo-mask-weight 0.8 --pseudo-mask-end-step 600"

DATA_DIR="$DATA_DIR" GPU="$GPU" MAX_STEPS="$MAX_STEPS" SEED="$SEED" \
VENV_PYTHON="$VENV_PYTHON" PLANB_INIT_NPZ="$PLANB_INIT_NPZ" EXTRA_TRAIN_ARGS="$EXTRA_TRAIN_ARGS" \
bash scripts/run_train_planb_init_selfcap.sh "$RESULT_DIR"
```

Expected (each run):
- `"$RESULT_DIR/stats/test_step0599.json"` exists
- `"$RESULT_DIR/cfg.yml"` contains:
  - `pseudo_mask_npz: <.../pseudo_masks_static_from_dyn_p99.npz>`
  - `pseudo_mask_weight: 0.8`
  - `pseudo_mask_end_step: 600`
  - same `init_npz_path` as the baseline of the same seed

Hard check (each run):
```bash
rg -n "^seed:|^init_npz_path:|^pseudo_mask_npz:|^pseudo_mask_weight:|^pseudo_mask_end_step:" "$RESULT_DIR/cfg.yml"
```

---

## Task 4 — Compute masked metrics for all 4 runs (foreground eval)

For each result dir (baseline/treatment × 2 seeds), run:
```bash
set -euo pipefail

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
DATA_DIR="$REPO_ROOT/data/thuman4_subject00_8cam60f"

RESULT_DIR="$REPO_ROOT/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/_seedrep_planb_init_600_seed43"

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

Expected (each run):
- `"$RESULT_DIR/stats_masked/test_step0599.json"` exists

---

## Task 5 — Decision: is the “FG win” reproducible?

Run the following to print deltas per seed (edit the four paths if you renamed dirs):
```bash
python3 - <<'PY'
import json
from pathlib import Path

REPO = Path(".").resolve()
BASE = REPO / "outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f"

pairs = [
    ("seed43",
     BASE / "_seedrep_planb_init_600_seed43",
     BASE / "_seedrep_weak_staticp99_w0.8_600_seed43"),
    ("seed44",
     BASE / "_seedrep_planb_init_600_seed44",
     BASE / "_seedrep_weak_staticp99_w0.8_600_seed44"),
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

Decision rule:
- If `OVERALL_OK == True` (两对 seed 都 OK): **不请专家**，进入下一步“压 full-frame trade-off”的最小调参（例如调小 `pseudo_mask_weight` 或调度 early-only）。
- If `OVERALL_OK == False`: 基本可判定该设置对 fg 目标**不稳定**；建议带上 dossier + 本次复核结果去请专家（沟通效率最高）。

---

## Task 6 — Write down the outcome (audit note)

Create `notes/openproposal_preexpert_seedrep_staticp99.md` and paste:
- 4 个 run 的路径
- 每个 seed 的 `Δpsnr_fg / Δlpips_fg / ΔtLPIPS`
- 最终 `OVERALL_OK` 结论 + 下一步决策

(Optional) commit:
```bash
git add notes/openproposal_preexpert_seedrep_staticp99.md
git commit -m "docs(notes): pre-expert seed replication for weak staticp99"
```

