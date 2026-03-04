# OpenProposal Phase 2 — VGGT/Diff Pseudomask Mining (THUman4.0 s00)

Date: 2026-03-04 (UTC)
Scope: `docs/plans/2026-03-03-openproposal-phase2-vggt-pseudomask.md`

## 1) Frozen tags and command lines

Frozen tags (as required by Task 2):
- `openproposal_thuman4_s00_diff_q0.995_ds4_med3`
- `openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3`

### diff backend (frozen)

```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
OUT_DIR="outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3"
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend diff \
  --temporal_smoothing median3 \
  --overwrite
```

### vggt backend (frozen)

```bash
DATA_DIR="data/thuman4_subject00_8cam60f"
OUT_DIR="outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3"
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" scripts/cue_mining.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$OUT_DIR" \
  --frame_start 0 \
  --num_frames 60 \
  --mask_downscale 4 \
  --threshold_quantile 0.995 \
  --backend vggt \
  --temporal_smoothing median3 \
  --vggt_model_id "facebook/VGGT-1B" \
  --vggt_cache_dir "/root/autodl-tmp/cache/vggt" \
  --vggt_mode crop \
  --overwrite
```

Produced contracts (both tags):
- `pseudo_masks.npz`
- `quality.json`
- `viz/grid_frame000000.jpg`
- `viz/overlay_cam02_frame000000.jpg`

## 2) Mask semantics (must clarify)

Current pseudomask semantics is **foreground/dynamic ROI cue (silhouette-oriented heuristic)**.
It is **not** equivalent to a paper-level "dynamic-region mask" unless extra equivalence proof is provided.

## 3) QA summary (frozen tags)

### `quality.json` stop-loss fields

- diff `openproposal_thuman4_s00_diff_q0.995_ds4_med3`
  - `all_black=false`
  - `all_white=false`
  - `temporal_flicker_l1_mean=0.00032719498267397285`
- vggt `openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3`
  - `all_black=false`
  - `all_white=false`
  - `temporal_flicker_l1_mean=0.0004927138797938824`

### Additional sparsity diagnostics (local)

For frozen tags (`q0.995`):
- diff: `mean(mask01)=0.0006206059669915092`, `ratio(mask>=32)=0.0012232496419243408`, `ratio(mask>=128)=7.284382284382284e-06`
- vggt: `mean(mask01)=0.0006215579739647797`, `ratio(mask>=32)=0.0013906192321889996`, `ratio(mask>=128)=5.147771317829457e-05`

Interpretation:
- Both avoid full-black/full-white collapse by stop-loss flags.
- Under evaluator default threshold (`mask_thr=0.5`, i.e. 128/255), masks are extremely sparse.

## 4) Visual inspection examples (local paths only)

Baseline visual entrypoints (plan-required):
- `outputs/cue_mining/openproposal_thuman4_s00_diff_q0.995_ds4_med3/viz/grid_frame000000.jpg`
- `outputs/cue_mining/openproposal_thuman4_s00_vggt1b_depthdiff_q0.995_ds4_med3/viz/grid_frame000000.jpg`

To make "success/failure" interpretable, additional local comparison overlays were generated at:
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/`
  - legend in `*_gt_pred_compare.jpg`: green=GT fg, red=pred-only, yellow=overlap

Success examples (3-5):
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/success_diff_t52_c06_gt_pred_compare.jpg`
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/success_diff_t43_c03_gt_pred_compare.jpg`
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/success_diff_t49_c05_gt_pred_compare.jpg`
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/success_vggt_t51_c07_gt_pred_compare.jpg`

Failure examples (1-2):
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/failure_vggt_t30_c06_gt_pred_compare.jpg`
- `outputs/qualitative_local/openproposal_phase2_vggt_pseudomask/failure_vggt_t30_c09_gt_pred_compare.jpg`

Observation summary:
- diff backend has multiple frames where high-confidence activation overlaps the body silhouette.
- vggt backend shows recurring background-highlight/reflective-region false positives on this scene.

## 5) `miou_fg` health-check (dataset masks as GT)

Anchor run:
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`

Commands executed (plan Task 4) generated:
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_miou_diff.json`
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_miou_vggt.json`

Key fields:
- diff (`q0.995`): `miou_fg = 0.0`
- vggt (`q0.995`): `miou_fg = 2.673510854454069e-06`

Interpretation:
- Health-check did not indicate useful fg agreement under default evaluator threshold 0.5.
- This is consistent with sparsity diagnostics and observed vggt background leakage.

## 6) Stop-loss retunes (allowed 1-2 tries, local)

Due to poor visual semantics at `q0.995`, two additional quantile retunes were run:
- Retry 1: `q0.990`
  - diff tag: `openproposal_thuman4_s00_diff_q0.990_ds4_med3`
  - vggt tag: `openproposal_thuman4_s00_vggt1b_depthdiff_q0.990_ds4_med3`
- Retry 2: `q0.950`
  - diff tag: `openproposal_thuman4_s00_diff_q0.950_ds4_med3`
  - vggt tag: `openproposal_thuman4_s00_vggt1b_depthdiff_q0.950_ds4_med3`

Result summary:
- Coverage increases with lower quantile, but vggt branch still has dominant background false positives on checked views.
- This note keeps frozen-tag outputs (`q0.995`) as Phase 2 contract and records retune traces for Phase 3 decision-making.

## 7) Compliance note

This phase stayed in local-eval mode:
- no dataset frames/GT masks were added to git or report pack
- all qualitative evidence stays under local `outputs/` paths
