# OpenProposal Phase 1 — Dataset + Masked Metrics Note

## Data source and compliance

- Dataset target: THUman4.0 subject-level subset (`subject00`, 8 cameras, 60 frames).
- This phase is **local-eval only**:
  - do not commit THUman frames/masks under `data/`;
  - do not commit run outputs under `outputs/`;
  - do not export GT images/masks/GT-comparison videos into `docs/report_pack/**`.
- Local qualitative artifacts are allowed under `outputs/qualitative_local/**` only.

## Mask source and binarization

- Default mask source is dataset-provided foreground matte (`data/.../masks/<cam>/<frame>.png`).
- Evaluator threshold for binary foreground is fixed to `0.5` (`--mask_thr 0.5` by default).
- When pseudo masks are used (Phase 2+), masks are loaded from `pseudo_masks.npz`, resized to render resolution, then thresholded with the same rule.

## Metric definitions

- Full-frame metrics are read from trainer stats (`psnr`, `ssim`, `lpips`, `tlpips`).
- Foreground-masked metrics are computed offline from trainer render canvases (`GT|Pred` concatenated):
  1. split canvas into GT (left half) and Pred (right half);
  2. derive foreground bbox from mask with margin (`bbox_margin_px`, default 32);
  3. crop GT/Pred to bbox;
  4. fill-black outside binary foreground mask within the crop;
  5. compute `psnr_fg` and `lpips_fg` on masked crops.
- Optional `miou_fg` is supported when GT mask + pseudo mask are both available.

## Phase 1 gate status (2026-03-03)

- **Code gate (repo-level): PASS**
  - `scripts/adapt_thuman4_release_to_freetime.py` + contract test pass.
  - `scripts/eval_masked_metrics.py` + contract test pass.
  - `docs/protocols/protocol_v3_openproposal.yaml` and COLMAP runbook are in place.
- **Local THUman smoke gate (dataset/cuda required): PENDING**
  - Blocker: THUman4.0 local subject path is not present in this workspace session.
  - To close gate, execute Task 6 run commands from `docs/plans/2026-03-03-openproposal-phase1-dataset-metrics.md` on a machine with local THUman data and GPU training budget.

## Repro checklist to close local smoke gate

1. Adapt THUman subject to `data/thuman4_subject00_8cam60f`.
2. Build `sparse/0` via reference-frame COLMAP runbook.
3. Export `triangulation/points3d_frame000000.npy`.
4. Run `run_train_planb_init_selfcap.sh` with `MAX_STEPS=600`.
5. Run `scripts/eval_masked_metrics.py` to emit `stats_masked/test_step0599.json`.
