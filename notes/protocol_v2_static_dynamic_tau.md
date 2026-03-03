# Protocol v2 static/dynamic tau selection (planb_init_600)

## Velocity stats reference (step599)

Source: `notes/velocity_stats_planb_init_600.md`

- `p50(||v||) = 0.075436`
- `p90(||v||) = 0.138472`

Chosen A/B candidates:
- `tau_low = 0.075436`
- `tau_high = 0.138472`

## A/B exports

### tau_low = 0.075436
- static-only: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- dynamic-only: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- filter log summary:
  - static_only kept `46374/92749 (0.500)`
  - dynamic_only kept `46375/92749 (0.500)`

### tau_high = 0.138472
- static-only: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.138472/videos/traj_4d_step599.mp4`
- dynamic-only: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.138472/videos/traj_4d_step599.mp4`
- filter log summary:
  - static_only kept `83474/92749 (0.900)`
  - dynamic_only kept `9275/92749 (0.100)`

## Decision

- `tau_final = 0.075436`
- Rationale: compared with `tau_high`, `tau_low` keeps a stronger dynamic branch (not overly sparse) while still removing a large share of movers from the static branch.

Final paths for talk/paper:
- static-only final: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- dynamic-only final: `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`

Known failure case:
- very slow movers can still leak into static-only at this threshold; conversely, small jittering background regions may leak into dynamic-only.

## Repro notes

In this environment, export used two extra runtime knobs for compatibility:
- `--init-npz-path outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz`
- `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1`
