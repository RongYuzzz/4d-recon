# Anti-Cherrypick Appendix: seg600_660 (Owner A)

- Date: 2026-02-26
- Scope: smoke200 evidence only (`MAX_STEPS=200`), no new full600

## Data generation (frame_start=600)

- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/adapt_selfcap_release_to_freetime.py --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz --output_dir data/selfcap_bar_8cam60f_seg600_660 --camera_ids 02,03,04,05,06,07,08,09 --frame_start 600 --num_frames 60 --image_downscale 2 --seed 0 --overwrite`

## Gate-S1 key fields

- `match_ratio_over_eligible = 0.586329`
- `clip_threshold_m_per_frame = 0.011418`
- canonical `clip_threshold_m_per_frame = 0.010881`
- threshold ratio vs canonical = `1.0493x` (well below 10x guard)
- `n_clipped = 495`
- Gate-S1 verdict: PASS

## Smoke200 comparison (test@step199)

Baseline (`baseline_smoke200`):
- PSNR `12.5846786499`, LPIPS `0.6267610192`, tLPIPS `0.0863862783`

Plan-B (`planb_init_smoke200`):
- PSNR `12.7752170563`, LPIPS `0.5779262781`, tLPIPS `0.0338712260`

Delta (planb - baseline):
- `ΔPSNR = +0.1905384064`
- `ΔLPIPS = -0.0488347411`
- `ΔtLPIPS = -0.0525150523` (relative `-60.7910%`)

## One-line trend conclusion

seg600_660 smoke200 keeps the same direction as canonical/seg200_260/seg400_460: Plan-B init improves LPIPS and tLPIPS with a positive PSNR delta, so this slice can be added as anti-cherrypick evidence.
