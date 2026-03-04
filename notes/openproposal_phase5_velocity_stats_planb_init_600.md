# Velocity Statistics

- init npz: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/thuman4_subject00_8cam60f/init_points_planb_step5.npz`
- ckpt: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/ckpts/ckpt_599.pt`

## step0 (init npz)

- `||v||` stats: min=0.000000, mean=0.000000, p50=0.000000, p90=0.000000, p99=0.000000, max=0.000000
- `ratio(||v|| < eps)`: 1.000000 (eps=1.0e-04)
- `times min/mean/max`: min=0.000000, mean=0.454189, max=0.916667
- `durations min/mean/max`: min=0.250000, mean=0.250000, max=0.250000

## step599 (ckpt)

- `||v||` stats: min=0.000000, mean=0.073896, p50=0.070611, p90=0.133772, p99=0.192386, max=0.465802
- `ratio(||v|| < eps)`: 0.081597 (eps=1.0e-04)
- `times min/mean/max`: min=-0.086237, mean=0.456650, max=1.069242
- `durations min/mean/max`: min=0.027678, mean=0.232242, max=3.702410

注：checkpoint 中的 `durations` 为 log-duration，本报告已做 `exp()` 还原后再统计。
