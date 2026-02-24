# Midterm Experiment Matrix (Owner C)

## Fixed Input
- Dataset root: `data/selfcap_bar_8cam60f`
- Triangulation input: `data/selfcap_bar_8cam60f/triangulation`

## Fixed Core Params
- `START_FRAME=0`
- `END_FRAME=60`
- `KEYFRAME_STEP=5`
- `CONFIG=default_keyframe_small`

## Naming Convention
- Baseline 600-step: `outputs/gate1_selfcap_baseline_600`
- Baseline control (optional): `outputs/gate1_selfcap_baseline_200_gs6`
- Ours weak (wait A/B merge): `outputs/gate1_selfcap_ours_weak_600`
- Ours strong (wait A/B merge): `outputs/gate1_selfcap_ours_strong_600`

## Minimum Required Deliverables (This Round)
- 1 baseline 600-step run with video + stats.
- 1 offline evidence tarball with `manifest_sha256.csv`.
- >=2 failure cases with mechanism-level explanation.

## Command 1: Baseline 600-step (GPU2)
```bash
cd /root/projects/4d-recon
MAX_STEPS=600 EVAL_STEPS=600 SAVE_STEPS=600 RENDER_TRAJ_PATH=fixed \
bash third_party/FreeTimeGsVanilla/run_pipeline.sh \
  data/selfcap_bar_8cam60f/triangulation data/selfcap_bar_8cam60f \
  outputs/gate1_selfcap_baseline_600 0 60 5 2 default_keyframe_small
```

## Command 2: Refresh Report Pack CSV
```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

## Command 3: Build Offline Evidence Tar
```bash
cd /root/projects/4d-recon
python3 scripts/pack_evidence.py \
  --outputs_root outputs \
  --out_tar outputs/midterm_evidence_2026-02-24.tar.gz
```

## Quick Checks
```bash
test -f outputs/gate1_selfcap_baseline_600/videos/traj_4d_step599.mp4
test -f outputs/gate1_selfcap_baseline_600/stats/val_step0599.json
test -f outputs/report_pack/metrics.csv
test -f outputs/midterm_evidence_2026-02-24.tar.gz
```
