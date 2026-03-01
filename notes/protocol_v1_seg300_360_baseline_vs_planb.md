# Protocol v1 seg300_360: baseline vs planb_init (full600)

Date: 2026-03-01

## Run directories

- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600`
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600`

## Video paths

- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600/videos/traj_4d_step599.mp4`

## What it shows / limitation

At step 599 on this second segment, `planb_init_600` improves both fidelity and temporal consistency over `baseline_600` (PSNR +1.54, tLPIPS -0.014 by the segment scoreboard). The qualitative videos are consistent with this direction and show cleaner dynamic reconstruction with less temporal instability. Limitation: this is a single-scene, single-segment check, so it should be interpreted as minimal generalization evidence rather than broad cross-scene validation.
