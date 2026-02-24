# Velocity Statistics

- init npz: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/keyframes_60frames_step5.npz`
- ckpt: `/root/autodl-tmp/projects/4d-recon/outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/ckpts/ckpt_599.pt`

## step0 (init npz)

- `||v||` stats: min=0.000000, mean=0.016971, p50=0.009839, p90=0.035429, p99=0.111240, max=0.499569
- `ratio(||v|| < eps)`: 0.000733 (eps=1.0e-04)
- `times min/mean/max`: min=0.000000, mean=0.454189, max=0.916667
- `durations min/mean/max`: min=0.250000, mean=0.250000, max=0.250000

## step599 (ckpt)

- `||v||` stats: min=0.000000, mean=0.251466, p50=0.165151, p90=0.491313, p99=1.504120, max=6.766573
- `ratio(||v|| < eps)`: 0.000108 (eps=1.0e-04)
- `times min/mean/max`: min=-0.152983, mean=0.455467, max=1.053088
- `durations min/mean/max`: min=0.027513, mean=0.261494, max=4.288943

注：checkpoint 中的 `durations` 为 log-duration，本报告已做 `exp()` 还原后再统计。
