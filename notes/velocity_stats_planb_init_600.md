# Velocity Statistics

- init npz: `/root/autodl-tmp/projects/4d-recon/outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- ckpt: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/planb_init_600/ckpts/ckpt_599.pt`

## step0 (init npz)

- `||v||` stats: min=0.000000, mean=0.001037, p50=0.000361, p90=0.002970, p99=0.008722, max=0.010881
- `ratio(||v|| < eps)`: 0.447584 (eps=1.0e-04)
- `times min/mean/max`: min=0.000000, mean=0.454189, max=0.916667
- `durations min/mean/max`: min=0.250000, mean=0.250000, max=0.250000

## step599 (ckpt)

- `||v||` stats: min=0.000000, mean=0.079964, p50=0.075436, p90=0.138472, p99=0.202537, max=0.548200
- `ratio(||v|| < eps)`: 0.015882 (eps=1.0e-04)
- `times min/mean/max`: min=-0.132359, mean=0.456422, max=1.151642
- `durations min/mean/max`: min=0.027717, mean=0.275496, max=2.418479

注：checkpoint 中的 `durations` 为 log-duration，本报告已做 `exp()` 还原后再统计。
