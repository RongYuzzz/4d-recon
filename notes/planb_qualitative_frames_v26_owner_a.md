# Plan-B v26 Qualitative Frames (Owner A)

- Date: 2026-02-26
- Frame root: `/root/projects/4d-recon/outputs/qualitative/planb_vs_baseline/frames_selected_v26`
- Rule: each clip exports `frame_000000`, `frame_000030`, `frame_000059` (frame 59 may fallback to last frame if clip shorter)

## Recommended hero frame groups (3 frames per clip)

### canonical (`planb_vs_baseline_step599`)

- `planb_vs_baseline_step599_frame_000000.jpg`
- `planb_vs_baseline_step599_frame_000030.jpg`
- `planb_vs_baseline_step599_frame_000059.jpg`
- Note: baseline side usually shows stronger blur/ghost around motion boundaries; planb keeps cleaner contours and more stable temporal appearance.

### seg200_260 (`planb_vs_baseline_seg200_260_step599`)

- `planb_vs_baseline_seg200_260_step599_frame_000000.jpg`
- `planb_vs_baseline_seg200_260_step599_frame_000030.jpg`
- `planb_vs_baseline_seg200_260_step599_frame_000059.jpg`
- Note: this slice is the strongest full600 gain case; use it to show both sharper details and reduced temporal flicker.

### seg300_360 (`planb_vs_baseline_seg300_360_step199`)

- `planb_vs_baseline_seg300_360_step199_frame_000000.jpg`
- `planb_vs_baseline_seg300_360_step199_frame_000030.jpg`
- `planb_vs_baseline_seg300_360_step199_frame_000059.jpg`
- Note: smoke200 setting still shows clear reduction of motion tailing and frame-to-frame instability under planb.

### seg400_460 (`planb_vs_baseline_seg400_460_step199`)

- `planb_vs_baseline_seg400_460_step199_frame_000000.jpg`
- `planb_vs_baseline_seg400_460_step199_frame_000030.jpg`
- `planb_vs_baseline_seg400_460_step199_frame_000059.jpg`
- Note: compare fast-moving parts; planb suppresses obvious transient artifacts while keeping structure more coherent.

### seg600_660 (`planb_vs_baseline_seg600_660_step199`)

- `planb_vs_baseline_seg600_660_step199_frame_000000.jpg`
- `planb_vs_baseline_seg600_660_step199_frame_000030.jpg`
- `planb_vs_baseline_seg600_660_step199_frame_000059.jpg`
- Note: good supplementary smoke200 example showing consistent LPIPS/tLPIPS direction and reduced temporal shimmer.

### seg1800_1860 (`planb_vs_baseline_seg1800_1860_step199`)

- `planb_vs_baseline_seg1800_1860_step199_frame_000000.jpg`
- `planb_vs_baseline_seg1800_1860_step199_frame_000030.jpg`
- `planb_vs_baseline_seg1800_1860_step199_frame_000059.jpg`
- Note: stress-test style segment; planb keeps temporal smoothness advantage and fewer frame-local artifacts.

