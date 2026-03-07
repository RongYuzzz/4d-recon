# V2.5 Bridge Experiments Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用 3 个桥接型中等实验，把当前项目从偏保守的 `v2` 提升到更接近原版开题三条主线的 `v2.5`，在不重开大规模高风险训练的前提下，显著增强“工作量饱满 + 有一点创新性”的证据强度。

**Architecture:** 本计划只允许一项中预算训练，其余两项都是“可解释 + 可量化”的桥接分析。Experiment 1 在 `THUman4` 上把 `VGGT cue` 变成有阈值扫与边界表的 weak cue 证据；Experiment 2 在 `SelfCap` 上用 `KLT` 给 token-topk correspondence 提供低成本 pseudo-reference；Experiment 3 在 `SelfCap` 上做 `ungated vs framediff-gated` 的 timeboxed `400-step` 配对训练，用最小成本把原版“时空关联约束”往前推进一格。

**Tech Stack:** Markdown docs, Python analysis scripts, Bash runners, existing `cue_mining.py`, existing `extract_temporal_correspondences_klt.py`, existing `run_train_planb_feature_loss_v2_selfcap.sh`, `pytest`, existing report-pack assets.

---

## Scope guardrails

- 只做以下三项：`THUman4 cue quantization`、`SelfCap token-topk vs KLT probe`、`SelfCap framediff-gated 400-step paired run`。
- 不重开 `oracle-weak`，不做新的 `full600` 多 seed 大扫参，不扩张到多数据集主线对比。
- 新结论必须继续遵守：`Plan-B` 是主线硬结果；`stage-2` 只有在证据足够时才能从 `Exploratory/Partial` 上调。
- `outputs/` 仅新增目录；不得手改历史结果。
- 若 Experiment 3 在 `seed42 @ step199` 已显著不如对照，则立即 timebox 停止，不继续加码。

---

### Task 0: Create isolated worktree and verify anchors

**Files:**
- Read: `AGENTS.md`
- Read: `4D-Reconstruction.md`
- Read: `4D-Reconstruction-v2.md`
- Read: `docs/plans/2026-03-06-v25-bridge-experiments-design.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Create a dedicated worktree for the bridge experiments and enter it**

Run:
```bash
export MAIN_REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$MAIN_REPO_ROOT"
git worktree add .worktrees/owner-b-20260306-v25-bridge -b feat/v25-bridge-experiments
cd .worktrees/owner-b-20260306-v25-bridge
pwd
```

Expected: a new isolated worktree exists at `.worktrees/owner-b-20260306-v25-bridge`, all subsequent commands in this plan are executed from that worktree root, and if the branch/path already exists from a previous attempt you should choose a fresh suffix before continuing.

**Step 2: Pin the shared Python environment for worktree execution**

Run:
```bash
export VENV_PYTHON="${VENV_PYTHON:-$MAIN_REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
export CUE_PYTHON="${CUE_PYTHON:-$VENV_PYTHON}"
[ -x "$VENV_PYTHON" ]
```

Expected: `VENV_PYTHON` points to the main repo's FreeTimeGsVanilla virtualenv Python, `CUE_PYTHON` reuses the same interpreter, and both work even though a fresh worktree may not contain its own `.venv`.

**Step 3: Verify the three current evidence anchors exist before adding new work**

Run:
```bash
[ -f docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md ]
[ -f notes/protocol_v2_vggt_cue_viz.md ]
[ -f notes/protocol_v2_sparse_corr_viz.md ]
[ -f notes/protocol_v2_stage2_tradeoff_qual.md ]
```

Expected: all files exist; this confirms the current `v2` baseline is intact before moving to `v2.5`.

**Step 4: Freeze the current thesis boundary in one sentence**

Write this sentence into the work log before coding:

```text
本轮目标不是证明 stage-2 已稳定全面更优，而是为原版三条研究主线各补一份更硬的桥接证据。
```

Expected: the execution session keeps this as the non-negotiable guardrail.

---

### Task 1: Add a THUman4 pseudo-mask alignment evaluator

**Files:**
- Create: `scripts/eval_pseudo_mask_dataset_alignment.py`
- Create: `scripts/tests/test_eval_pseudo_mask_dataset_alignment_contract.py`
- Read: `scripts/cue_mining.py`
- Read: `scripts/tests/test_cue_mining_quality_stats.py`
- Read: `scripts/eval_masked_metrics.py`

**Step 1: Write the failing contract test**

Create `scripts/tests/test_eval_pseudo_mask_dataset_alignment_contract.py` with a toy dataset containing:
- `images/02/*.jpg`, `images/03/*.jpg`
- `masks/02/*.png`, `masks/03/*.png`
- a toy `pseudo_masks.npz`

The test must assert the script writes:
- `summary.json`
- `threshold_sweep.csv`

And that `summary.json` contains at least:
```python
{
    "best_threshold",
    "best_miou_fg",
    "best_precision_fg",
    "best_recall_fg",
    "pred_fg_coverage",
    "gt_fg_coverage",
    "temporal_flicker_l1_mean",
}
```

**Step 2: Run the test to verify it fails first**

Run:
```bash
pytest -q scripts/tests/test_eval_pseudo_mask_dataset_alignment_contract.py -q
```

Expected: FAIL because `scripts/eval_pseudo_mask_dataset_alignment.py` does not exist yet.

**Step 3: Implement the evaluator script**

Create `scripts/eval_pseudo_mask_dataset_alignment.py` with these requirements:
- Inputs:
  - `--data_dir`
  - `--pred_mask_npz`
  - `--out_dir`
  - `--mask_thresholds` (comma-separated, e.g. `0.05,0.10,...,0.95`)
  - `--gt_alpha_threshold` (default `127`)
- Contract:
  - load `pseudo_masks.npz:masks`
  - load dataset `masks/*.png`
  - downsample/align GT mask to pseudo-mask spatial size if needed
  - compute per-threshold `miou_fg`, `precision_fg`, `recall_fg`, `pred_fg_coverage`, `gt_fg_coverage`
  - compute one global `temporal_flicker_l1_mean` from predicted masks
  - write `threshold_sweep.csv` and `summary.json`
- Safety:
  - fail loudly if camera ids or frame counts do not align
  - treat THUman4 alpha masks as grayscale mattes and binarize by `gt_alpha_threshold`

**Step 4: Run the contract test again**

Run:
```bash
pytest -q scripts/tests/test_eval_pseudo_mask_dataset_alignment_contract.py -q
```

Expected: PASS.

**Step 5: Run adjacent cue tests to avoid breaking existing behavior**

Run:
```bash
pytest -q scripts/tests/test_cue_mining_contract.py scripts/tests/test_cue_mining_quality_stats.py -q
```

Expected: PASS.

---

### Task 2: Execute THUman4 cue quantization and write the note

**Files:**
- Create: `notes/2026-03-06-thuman4-vggt-cue-quant.md`
- Create: `outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/`
- Read: `notes/protocol_v2_vggt_cue_viz.md`
- Read: `docs/reviews/2026-03-05/expert-diagnosis-dossier_phase3-4-6.md`

**Step 1: Run VGGT cue mining on THUman4 with a fresh append-only tag**

Run:
```bash
CUE_PYTHON="$VENV_PYTHON" bash scripts/run_cue_mining.sh \
  data/thuman4_subject00_8cam60f \
  thuman4_subject00_8cam60f_vggt_probe_v25 \
  0 60 vggt 4
```

Expected: a new directory `outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/` is created with `pseudo_masks.npz`, `quality.json`, and `viz/`.

**Step 2: Run threshold-sweep alignment evaluation**

Run:
```bash
"$VENV_PYTHON" scripts/eval_pseudo_mask_dataset_alignment.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --pred_mask_npz outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/pseudo_masks.npz \
  --out_dir outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/alignment_eval \
  --mask_thresholds 0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50,0.60,0.70,0.80,0.90 \
  --gt_alpha_threshold 127
```

Expected: `summary.json` and `threshold_sweep.csv` are written under `alignment_eval/`.

**Step 3: Write the experiment note**

Create `notes/2026-03-06-thuman4-vggt-cue-quant.md` with sections:
- `Why THUman4 is used`
- `Exact command`
- `Threshold sweep result`
- `Best threshold snapshot`
- `What this proves`
- `Failure boundary`

Required wording constraints:
- must explicitly say this evaluates `weak cue alignment`, not full segmentation performance;
- must explicitly mention THUman4 masks are alpha mattes binarized at `127` for this audit;
- must not claim the result transfers automatically to SelfCap.

**Step 4: Verify required artifacts exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/pseudo_masks.npz'),
    Path('outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/quality.json'),
    Path('outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/alignment_eval/summary.json'),
    Path('outputs/cue_mining/thuman4_subject00_8cam60f_vggt_probe_v25/alignment_eval/threshold_sweep.csv'),
    Path('notes/2026-03-06-thuman4-vggt-cue-quant.md'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 3: Add a token-topk vs KLT evaluator

**Files:**
- Create: `scripts/eval_tokenproj_temporal_topk_against_klt.py`
- Create: `scripts/tests/test_eval_tokenproj_temporal_topk_against_klt_contract.py`
- Read: `scripts/viz_tokenproj_temporal_topk.py`
- Read: `scripts/extract_temporal_correspondences_klt.py`
- Read: `scripts/tests/test_temporal_correspondences_klt_contract.py`

**Step 1: Write the failing contract test**

Create `scripts/tests/test_eval_tokenproj_temporal_topk_against_klt_contract.py` with a synthetic cache + synthetic KLT NPZ where the correct token displacement is known.

The test must assert that the script writes:
- `summary.json`
- `pair_metrics.csv`

And that `summary.json` includes at least:
```python
{
    "num_pairs",
    "top1_cell_hit_rate",
    "topk_cell_hit_rate",
    "local_window_hit_rate",
    "mean_best_cosine",
    "unique_dst_ratio",
}
```

**Step 2: Run the test to verify it fails first**

Run:
```bash
pytest -q scripts/tests/test_eval_tokenproj_temporal_topk_against_klt_contract.py -q
```

Expected: FAIL because the evaluator does not exist yet.

**Step 3: Implement the evaluator script**

Create `scripts/eval_tokenproj_temporal_topk_against_klt.py` with these requirements:
- Inputs:
  - `--cache_npz`
  - `--klt_npz`
  - `--out_dir`
  - `--topk` (default `20`)
  - `--local_radius_tokens` (default `1`)
  - `--camera_ids` (optional filter)
  - `--frames` (optional subset)
- Logic:
  - map KLT source/destination pixel coordinates to token-grid cells
  - compute token cosine similarity from `phi`
  - for each source token cell, rank destination token cells by cosine similarity
  - evaluate whether the KLT destination cell is the top1 match, in top-k, or within a local radius window
  - compute `mean_best_cosine` and `unique_dst_ratio`
- Outputs:
  - `summary.json`
  - `pair_metrics.csv`
- Safety:
  - validate shape compatibility between cache metadata and KLT metadata

**Step 4: Run the new test and adjacent KLT test**

Run:
```bash
pytest -q \
  scripts/tests/test_eval_tokenproj_temporal_topk_against_klt_contract.py \
  scripts/tests/test_temporal_correspondences_klt_contract.py -q
```

Expected: PASS.

---

### Task 4: Execute SelfCap token-topk vs KLT correspondence audit

**Files:**
- Create: `notes/2026-03-06-selfcap-tokenproj-klt-alignment.md`
- Create: `outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/`
- Read: `notes/protocol_v2_sparse_corr_viz.md`
- Read: `outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/meta.json`

**Step 1: Extract KLT pseudo-reference on SelfCap**

Run:
```bash
"$VENV_PYTHON" scripts/extract_temporal_correspondences_klt.py \
  --data_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,05,09 \
  --frame_start 0 \
  --num_frames 60 \
  --max_tracks_per_pair 500 \
  --min_track_len 1 \
  --fb_err_thresh 1.5 \
  --fb_weight_sigma 1.5 \
  --fb_weight_min 0.05 \
  --out_npz outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/selfcap_klt_pairs.npz \
  --viz_dir outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/klt_viz
```

Expected: KLT NPZ and at least one viz image exist.

**Step 2: Run token-topk vs KLT evaluation**

Run:
```bash
"$VENV_PYTHON" scripts/eval_tokenproj_temporal_topk_against_klt.py \
  --cache_npz outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
  --klt_npz outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/selfcap_klt_pairs.npz \
  --out_dir outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/eval \
  --camera_ids 02,05,09 \
  --frames 0,30 \
  --topk 20 \
  --local_radius_tokens 1
```

Expected: `summary.json` and `pair_metrics.csv` exist under `eval/`.

**Step 3: Write the audit note**

Create `notes/2026-03-06-selfcap-tokenproj-klt-alignment.md` with sections:
- `Why KLT is used as a pseudo-reference`
- `Exact command`
- `Summary metrics`
- `What this proves`
- `What it still does not prove`
- `Failure boundary`

Required wording constraints:
- must explicitly say KLT is a low-cost pseudo-reference, not GT correspondence;
- must explicitly say this is an audit for the original proposal’s correspondence route;
- must not claim this directly proves stage-2 gain.

**Step 4: Verify output packet exists**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/selfcap_klt_pairs.npz'),
    Path('outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/eval/summary.json'),
    Path('outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v25/eval/pair_metrics.csv'),
    Path('notes/2026-03-06-selfcap-tokenproj-klt-alignment.md'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 5: Add a framediff-gated 400-step paired runner

**Files:**
- Create: `scripts/run_planb_feat_v2_framediff400_pair.sh`
- Create: `scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py`
- Read: `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
- Read: `scripts/run_train_feature_loss_v2_gated_selfcap.sh`
- Read: `scripts/tests/test_run_train_planb_feature_loss_v2_script_exists.py`

**Step 1: Write the contract test first**

Create `scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py` that asserts the new shell runner contains these tokens:
- `MAX_STEPS=400`
- `SEEDS=42,43`
- `VGGT_FEAT_GATING=none`
- `VGGT_FEAT_GATING=framediff`
- `VGGT_FEAT_GATING_TOP_P=0.10`
- `EVAL_STEPS=199,399`
- `SAVE_STEPS=199,399`

**Step 2: Run the test to verify it fails first**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py -q
```

Expected: FAIL because the runner does not exist yet.

**Step 3: Implement the paired runner**

Create `scripts/run_planb_feat_v2_framediff400_pair.sh` with:
- `set -euo pipefail`
- loop over `SEEDS=42,43`
- for each seed run:
  - one `ungated` job via `scripts/run_train_planb_feature_loss_v2_selfcap.sh`
  - one `gated` job via the same runner with `VGGT_FEAT_GATING=framediff` and `VGGT_FEAT_GATING_TOP_P=0.10`
- fixed schedule defaults:
  - `MAX_STEPS=400`
  - `LAMBDA_VGGT_FEAT=0.005`
  - `VGGT_FEAT_START_STEP=150`
  - `VGGT_FEAT_RAMP_STEPS=150`
  - `VGGT_FEAT_EVERY=16`
  - `EVAL_STEPS=199,399`
  - `SAVE_STEPS=199,399`
- output root default:
  - `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_framediff400_pair/`

**Step 4: Re-run the contract test**

Run:
```bash
pytest -q scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py -q
```

Expected: PASS.

---

### Task 6: Execute the framediff-gated paired training and summarize it

**Files:**
- Create: `notes/2026-03-06-selfcap-planb-feat-v2-framediff400-pair.md`
- Read: `scripts/analyze_temporal_diff_from_renders.py`
- Read: `scripts/analyze_vggt_gate_framediff.py`
- Read: `docs/report_pack/2026-02-27-v2/scoreboard.md`

**Step 1: Run the paired 400-step driver**

Run:
```bash
bash scripts/run_planb_feat_v2_framediff400_pair.sh
```

Expected: 4 run directories are created under `outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_framediff400_pair/`.

**Step 2: Apply the timebox stop rule after the first seed if necessary**

Check `seed42` at `step199`:
- if `gated` is clearly worse than `ungated` on both `LPIPS` and `tLPIPS`, do not expand scope beyond the planned pair;
- still finish the paired design if already started, but do not add new seeds or longer runs.

Expected: no scope creep beyond the pre-registered pair.

**Step 3: Summarize the pair results at 199/399**

Create `notes/2026-03-06-selfcap-planb-feat-v2-framediff400-pair.md` with:
- `Exact command`
- `Per-seed 199/399 table`
- `Mean delta gated - ungated`
- `What this says about the original correspondence/gating route`
- `Decision recommendation`

Required wording constraints:
- must explicitly separate `single-seed behavior` from `paired trend`;
- must explicitly state whether this is `promising / mixed / stop`;
- must not claim route-level breakthrough unless both seeds support it.

**Step 4: If gated looks visually different and both runs exported `test_step399_*.png`, run one targeted temporal-diff diagnostic**

Run only on the best illustrative pair, and only if both run directories contain `renders/test_step399_*.png` files. If renders were not exported, record that fact in the note and skip this optional diagnostic.

```bash
"$VENV_PYTHON" scripts/analyze_temporal_diff_from_renders.py \
  --renders_dir <ungated_run_dir>/renders \
  --pattern_prefix test_step399_ \
  --out_csv outputs/report_pack/diagnostics/v25_framediff_pair/ungated_temporal_diff_step399.csv

"$VENV_PYTHON" scripts/analyze_temporal_diff_from_renders.py \
  --renders_dir <gated_run_dir>/renders \
  --pattern_prefix test_step399_ \
  --out_csv outputs/report_pack/diagnostics/v25_framediff_pair/gated_temporal_diff_step399.csv

python3 - <<'PY'
import csv
from pathlib import Path

a = Path('outputs/report_pack/diagnostics/v25_framediff_pair/ungated_temporal_diff_step399.csv')
b = Path('outputs/report_pack/diagnostics/v25_framediff_pair/gated_temporal_diff_step399.csv')
out = Path('outputs/report_pack/diagnostics/v25_framediff_pair/delta_temporal_diff_step399.csv')
out.parent.mkdir(parents=True, exist_ok=True)
rows_a = list(csv.DictReader(a.open(encoding='utf-8')))
rows_b = list(csv.DictReader(b.open(encoding='utf-8')))
assert len(rows_a) == len(rows_b), (len(rows_a), len(rows_b))
with out.open('w', newline='', encoding='utf-8') as f:
    fieldnames = ['pair_idx', 'frame_prev', 'frame_cur', 'mean_abs_diff_ungated', 'mean_abs_diff_gated', 'delta_mean_abs_diff']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for xa, xb in zip(rows_a, rows_b):
        assert xa['pair_idx'] == xb['pair_idx']
        assert xa['frame_prev'] == xb['frame_prev']
        assert xa['frame_cur'] == xb['frame_cur']
        da = float(xa['mean_abs_diff'])
        db = float(xb['mean_abs_diff'])
        w.writerow({
            'pair_idx': xa['pair_idx'],
            'frame_prev': xa['frame_prev'],
            'frame_cur': xa['frame_cur'],
            'mean_abs_diff_ungated': f'{da:.8f}',
            'mean_abs_diff_gated': f'{db:.8f}',
            'delta_mean_abs_diff': f'{(db - da):.8f}',
        })
print(out)
PY
```

Expected: only one focused diagnostic packet is produced under `outputs/report_pack/diagnostics/v25_framediff_pair/`; do not expand to broad render sweeps.

**Step 5: If needed, export gate activation summary for the same cache**

Run:
```bash
"$VENV_PYTHON" scripts/analyze_vggt_gate_framediff.py \
  --cache_npz outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
  --out_dir outputs/report_pack/diagnostics/v25_gate_framediff
```

Expected: `gate_framediff_mean_by_frame.csv`, `gate_framediff_mean_by_view.csv`, and `gate_framediff_heatmap.png` exist.

---

### Task 7: Feed the new evidence back into the thesis entry pack

**Files:**
- Modify: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Modify: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `notes/2026-03-06-thuman4-vggt-cue-quant.md`
- Read: `notes/2026-03-06-selfcap-tokenproj-klt-alignment.md`
- Read: `notes/2026-03-06-selfcap-planb-feat-v2-framediff400-pair.md`

**Step 1: Update the VGGT soft-prior brief**

Add:
- one paragraph for `THUman4 cue quantization`;
- one paragraph for `SelfCap token-topk vs KLT`;
- one sentence updating whether stage-2 moved from `Partial` to `Partial (with gated evidence)` or stayed `Partial / Exploratory`.

**Step 2: Update the alignment table conservatively**

Only promote a row if the new evidence genuinely supports it. Example allowed changes:
- `VGGT latent cue mining` stays `Done` but becomes stronger with quantitative boundary evidence;
- `注意力/对应关系引导的时空一致约束` may move from `Exploratory` to `Partial` only if Experiment 2 + 3 together justify it.

**Step 3: Update the README single-entry summary**

Add one short block titled `What changed in v2.5` that lists the 3 new bridge experiments and their net effect on the thesis story.

**Step 4: Verify no overclaim was introduced**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/README.md').read_text(encoding='utf-8')
for bad in ['稳定全面优于', '已证明 stage-2 全面有效', '已完成完整 object editing']:
    assert bad not in text, bad
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 8: Final acceptance check

**Files:**
- Read: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `notes/2026-03-06-thuman4-vggt-cue-quant.md`
- Read: `notes/2026-03-06-selfcap-tokenproj-klt-alignment.md`
- Read: `notes/2026-03-06-selfcap-planb-feat-v2-framediff400-pair.md`

**Step 1: Verify all bridge deliverables exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    'scripts/eval_pseudo_mask_dataset_alignment.py',
    'scripts/tests/test_eval_pseudo_mask_dataset_alignment_contract.py',
    'scripts/eval_tokenproj_temporal_topk_against_klt.py',
    'scripts/tests/test_eval_tokenproj_temporal_topk_against_klt_contract.py',
    'scripts/run_planb_feat_v2_framediff400_pair.sh',
    'scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py',
    'notes/2026-03-06-thuman4-vggt-cue-quant.md',
    'notes/2026-03-06-selfcap-tokenproj-klt-alignment.md',
    'notes/2026-03-06-selfcap-planb-feat-v2-framediff400-pair.md',
]
missing = [p for p in checks if not Path(p).exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

**Step 2: Run the targeted test suite**

Run:
```bash
pytest -q \
  scripts/tests/test_eval_pseudo_mask_dataset_alignment_contract.py \
  scripts/tests/test_eval_tokenproj_temporal_topk_against_klt_contract.py \
  scripts/tests/test_run_planb_feat_v2_framediff400_pair_contract.py \
  scripts/tests/test_temporal_correspondences_klt_contract.py \
  scripts/tests/test_cue_mining_contract.py \
  scripts/tests/test_cue_mining_quality_stats.py -q
```

Expected: PASS.

**Step 3: Re-answer the three thesis-critical questions**

The updated package should now let you answer “yes” to all three:
- Is there at least one more quantitative bridge from the original VGGT route to the current system?
- Is the correspondence route now supported by more than pictures alone?
- Is there one additional timeboxed training result that moves the project closer to the original proposal without reopening uncontrolled sweep risk?

Expected: all three should be defensibly `yes`.

**Step 4: Do not commit unless explicitly asked**

Expected: no `git commit` is made unless the user later requests it.
