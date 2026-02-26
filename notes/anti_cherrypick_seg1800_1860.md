# Anti-Cherrypick Appendix: seg1800_1860 (Owner A)

- Date: 2026-02-26
- Scope: smoke200 evidence only (`MAX_STEPS=200`), no new full600

## Data generation (frame_start=1800)

- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/adapt_selfcap_release_to_freetime.py --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz --output_dir data/selfcap_bar_8cam60f_seg1800_1860 --camera_ids 02,03,04,05,06,07,08,09 --frame_start 1800 --num_frames 60 --image_downscale 2 --seed 0 --overwrite`

## Gate-S1 key fields

- `match_ratio_over_eligible = 0.535983`
- `clip_threshold_m_per_frame = 0.017100`
- canonical `clip_threshold_m_per_frame = 0.010881`
- threshold ratio vs canonical = `1.5715x` (well below 10x guard)
- `n_clipped = 457`
- Gate-S1 verdict: PASS

## Smoke200 comparison (test@step199)

Baseline (`baseline_smoke200`):
- PSNR `12.5796127319`, LPIPS `0.6289873719`, tLPIPS `0.0888407901`

Plan-B (`planb_init_smoke200`):
- PSNR `12.7081241608`, LPIPS `0.5844914913`, tLPIPS `0.0355691463`

Delta (planb - baseline):
- `ΔPSNR = +0.1285114288`
- `ΔLPIPS = -0.0444958806`
- `ΔtLPIPS = -0.0532716438` (relative `-59.9630%`)

## One-line trend conclusion

seg1800_1860 smoke200 stays aligned with canonical/seg200_260/seg400_460/seg600_660: Plan-B init improves LPIPS and tLPIPS while keeping a positive PSNR delta, so this slice can be appended as anti-cherrypick evidence.
