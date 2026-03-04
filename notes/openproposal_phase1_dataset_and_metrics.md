# OpenProposal Phase 1 — Dataset + Masked Metrics Note

## Data source and compliance

- Dataset target: THUman4.0 subject-level subset (`subject00`, 8 cameras, 60 frames).
- Local source used in this run: `data/raw/thuman4/subject00` (camera mapping `cam01..cam08 -> 02..09`).
- License/compliance: THUman4.0 data follows original dataset terms; this repo only keeps local paths and derived metrics, and does not redistribute raw frames/masks.
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

## Phase 1 gate status (2026-03-04)

- **Code gate (repo-level): PASS**
  - `scripts/adapt_thuman4_release_to_freetime.py` + contract test pass.
  - `scripts/eval_masked_metrics.py` + contract test pass.
  - `docs/protocols/protocol_v3_openproposal.yaml` and COLMAP runbook are in place.
- **Local THUman smoke gate (dataset/cuda required): PASS**
  - Adapted scene: `data/thuman4_subject00_8cam60f` (`images/` + `masks/`, 8 cams × 60 frames).
  - COLMAP sparse: `data/thuman4_subject00_8cam60f/sparse/0/{cameras.bin,images.bin,points3D.bin}`.
  - Triangulation smoke: `data/thuman4_subject00_8cam60f/triangulation/points3d_frame000000.npy` (visible-per-frame mode).
  - Training smoke600 output: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600`.
  - Masked eval output: `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599.json`.
  - Key test metrics (step 599): `psnr=16.1520`, `ssim=0.5621`, `lpips=0.7325`, `tlpips=0.0071`.
  - Key masked metrics (step 599): `psnr_fg=16.8066`, `lpips_fg=0.0490`, `num_fg_frames=60`.

## Repro checklist (completed on 2026-03-04)

1. Adapt THUman subject to `data/thuman4_subject00_8cam60f`.
2. Build `sparse/0` via reference-frame COLMAP runbook.
3. Export `triangulation/points3d_frame000000.npy`.
4. Run `run_train_planb_init_selfcap.sh` with `MAX_STEPS=600`.
5. Run `scripts/eval_masked_metrics.py` to emit `stats_masked/test_step0599.json`.
