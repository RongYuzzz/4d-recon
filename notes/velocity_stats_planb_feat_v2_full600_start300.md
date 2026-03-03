# Velocity Statistics

- init npz: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- ckpt: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600_lam0.005_start300_ramp200_every16/ckpts/ckpt_599.pt`

## step0 (init npz)

- `||v||` stats: min=0.000000, mean=0.001037, p50=0.000361, p90=0.002970, p99=0.008722, max=0.010881
- `ratio(||v|| < eps)`: 0.447584 (eps=1.0e-04)
- `times min/mean/max`: min=0.000000, mean=0.454189, max=0.916667
- `durations min/mean/max`: min=0.250000, mean=0.250000, max=0.250000

## step599 (ckpt)

- `||v||` stats: min=0.000000, mean=0.080016, p50=0.075432, p90=0.139066, p99=0.201404, max=0.533901
- `ratio(||v|| < eps)`: 0.015882 (eps=1.0e-04)
- `times min/mean/max`: min=-0.220123, mean=0.456472, max=1.036744
- `durations min/mean/max`: min=0.027714, mean=0.274864, max=2.726396

注：checkpoint 中的 `durations` 为 log-duration，本报告已做 `exp()` 还原后再统计。

