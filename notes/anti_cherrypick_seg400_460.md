# Anti-Cherrypick Appendix: seg400_460 (Owner A)

- Date: 2026-02-26
- Scope: smoke200 evidence only (`MAX_STEPS=200`), no new full600

## Data generation (frame_start=400)

- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/adapt_selfcap_release_to_freetime.py --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz --output_dir data/selfcap_bar_8cam60f_seg400_460 --camera_ids 02,03,04,05,06,07,08,09 --frame_start 400 --num_frames 60 --image_downscale 2 --seed 0 --overwrite`

## Gate-S1 key fields

- `match_ratio_over_eligible = 0.5510144213`
- `clip_threshold_m_per_frame = 0.0135933962`
- canonical `clip_threshold_m_per_frame = 0.0108813836`
- threshold ratio vs canonical = `1.2492x` (well below 10x guard)
- `n_clipped = 470`
- Gate-S1 verdict: PASS

## Smoke200 comparison (test@step199)

Baseline (`baseline_smoke200`):
- PSNR `12.5888776779`, LPIPS `0.6276710629`, tLPIPS `0.0851773545`

Plan-B (`planb_init_smoke200`):
- PSNR `12.7610082626`, LPIPS `0.5838674903`, tLPIPS `0.0352740064`

Delta (planb - baseline):
- `ΔPSNR = +0.1721305847`
- `ΔLPIPS = -0.0438035727`
- `ΔtLPIPS = -0.0499033481` (relative `-58.5876%`)

## One-line trend conclusion

seg400_460 smoke200 continues the same direction as canonical and seg200_260: Plan-B init improves both appearance quality (LPIPS) and temporal consistency (tLPIPS), with no PSNR penalty.
