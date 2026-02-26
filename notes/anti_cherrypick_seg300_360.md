# Anti-Cherrypick Appendix: seg300_360 (Owner A)

- Date: 2026-02-26
- Scope: smoke200 evidence only (`MAX_STEPS=200`), no new full600

## Data generation (frame_start=300)

- `PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python`
- `scripts/adapt_selfcap_release_to_freetime.py --tar_gz /root/projects/4d-recon/data/raw/selfcap/bar-release.tar.gz --output_dir /root/projects/4d-recon/data/selfcap_bar_8cam60f_seg300_360 --camera_ids 02,03,04,05,06,07,08,09 --frame_start 300 --num_frames 60 --image_downscale 2 --seed 0 --overwrite`

## Template hygiene (Plan-B init template source)

- baseline template: `/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/_baseline_init/keyframes_60frames_step5.npz`
- init path: `/root/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f_seg300_360/init_points_planb_step5.npz`

## Gate-S1 key fields

- `match_ratio_over_eligible = 0.5955913473`
- `clip_threshold_m_per_frame = 0.0115640901`
- canonical `clip_threshold_m_per_frame = 0.0108813836`
- threshold ratio vs canonical = `1.0627x`
- `n_clipped = 507`
- Gate-S1 verdict: PASS

## Smoke200 comparison (test@step199)

Baseline (`baseline_smoke200`):
- PSNR `12.7534875870`, LPIPS `0.6217724085`, tLPIPS `0.0846709535`

Plan-B (`planb_init_smoke200`):
- PSNR `12.9346237183`, LPIPS `0.5720292926`, tLPIPS `0.0329684690`

Delta (planb - baseline):
- `ΔPSNR = +0.1811361313`
- `ΔLPIPS = -0.0497431159`
- `ΔtLPIPS = -0.0517024845` (relative `-61.0628%`)

## One-line trend conclusion

seg300_360 与 canonical/seg200_260/seg400_460/seg600_660/seg1800_1860 同向：Plan-B init 在 smoke200 下改善 LPIPS 与 tLPIPS，且 PSNR 为正增益，建议纳入 anti-cherrypick 防守位。
