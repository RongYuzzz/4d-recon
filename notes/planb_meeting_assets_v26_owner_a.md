# Plan-B v26 Meeting Assets Manifest (Owner A)

- Date: 2026-02-26
- Scope: meeting qualitative clips + frame groups for writing/presentation
- Decision source: `docs/decisions/2026-02-26-planb-v26-freeze.md`
- Constraint reminder: no new training, no protocol/metric logic changes

## 1) Source videos (3)

1. Canonical full600:
   - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
   - Use: baseline vs planb mainline qualitative comparison
2. seg200_260 full600:
   - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
   - Use: strongest full600 slice evidence for onepager/table narrative
3. smoke200 example seg:
   - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`
   - Use: smoke200 supplemental evidence for anti-cherrypick defense

All 3 source videos are present and ffprobe-readable:

| Source | Duration (s) | Resolution | Size (bytes) |
| --- | ---: | --- | ---: |
| `planb_vs_baseline_step599.mp4` | 1.667 | 1920x1716 | 1813796 |
| `planb_vs_baseline_seg200_260_step599.mp4` | 1.667 | 1920x1716 | 1870938 |
| `planb_vs_baseline_seg400_460_step199.mp4` | 1.667 | 1920x1716 | 6757119 |

## 2) clips_v26 outputs (non-git path)

- Directory: `outputs/qualitative/planb_vs_baseline/clips_v26/`
- Per source: 2 variants generated
  - `_12s_copy.mp4` (stream copy)
  - `_12s_h264.mp4` (scaled/re-encoded for embed stability)

| Clip | Duration (s) | Resolution | Size (bytes) | Size (MB) |
| --- | ---: | --- | ---: | ---: |
| `planb_vs_baseline_step599_12s_copy.mp4` | 1.667 | 1920x1716 | 1813796 | 1.730 |
| `planb_vs_baseline_step599_12s_h264.mp4` | 1.667 | 1280x1144 | 405934 | 0.387 |
| `planb_vs_baseline_seg200_260_step599_12s_copy.mp4` | 1.667 | 1920x1716 | 1870938 | 1.784 |
| `planb_vs_baseline_seg200_260_step599_12s_h264.mp4` | 1.667 | 1280x1144 | 426347 | 0.407 |
| `planb_vs_baseline_seg400_460_step199_12s_copy.mp4` | 1.667 | 1920x1716 | 6757119 | 6.444 |
| `planb_vs_baseline_seg400_460_step199_12s_h264.mp4` | 1.667 | 1280x1144 | 1408325 | 1.343 |

Check: all clips are ffprobe-readable and each clip is below 30MB.

## 3) frames_selected_v26 recommended hero frames (non-git path)

- Directory: `outputs/qualitative/planb_vs_baseline/frames_selected_v26/`
- 3 frames per source (0/30/59 fallback-safe), total 9:

### canonical

- `frame_planb_vs_baseline_step599_000000.jpg`
- `frame_planb_vs_baseline_step599_000030.jpg`
- `frame_planb_vs_baseline_step599_000059.jpg`

### seg200_260

- `frame_planb_vs_baseline_seg200_260_step599_000000.jpg`
- `frame_planb_vs_baseline_seg200_260_step599_000030.jpg`
- `frame_planb_vs_baseline_seg200_260_step599_000059.jpg`

### seg400_460

- `frame_planb_vs_baseline_seg400_460_step199_000000.jpg`
- `frame_planb_vs_baseline_seg400_460_step199_000030.jpg`
- `frame_planb_vs_baseline_seg400_460_step199_000059.jpg`

## 4) Meeting playback order (<= 5 minutes)

1. `planb_vs_baseline_step599_12s_h264.mp4` (canonical)
2. `planb_vs_baseline_seg200_260_step599_12s_h264.mp4` (seg200_260 full600)
3. `planb_vs_baseline_seg400_460_step199_12s_h264.mp4` (smoke200 example)
4. If needed, freeze-frame compare from the 9 JPG files above

Expected total playback time for the 3 clips is about 5 seconds (plus presenter narration), safely within a 5-minute slot.

## 5) Integrity reminder

This plan only repackages existing qualitative outputs.  
No new training was run, and no metric/protocol definition was changed.

## 6) Optional slices (loop12s, anti-cherrypick follow-up)

Generated loop clips (h264, 12s) under:
`outputs/qualitative/planb_vs_baseline/clips_v26_looped/`

- `planb_vs_baseline_seg300_360_step199_loop12s_h264.mp4`
- `planb_vs_baseline_seg600_660_step199_loop12s_h264.mp4`
- `planb_vs_baseline_seg1800_1860_step199_loop12s_h264.mp4`

Generated freeze-frame covers under:
`outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`

- `planb_vs_baseline_seg300_360_step199_loop12s_h264_t6.jpg`
- `planb_vs_baseline_seg600_660_step199_loop12s_h264_t6.jpg`
- `planb_vs_baseline_seg1800_1860_step199_loop12s_h264_t6.jpg`

Use: on-demand backup evidence when anti-cherrypick questions target segments beyond canonical/seg200_260/seg400_460.

## 7) Offline bundle (local only, non-git artifact)

- Bundle path: `artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`
- SHA256:
  `89a17a3ad9987e006385aaaee3c25fa00f6e5c4fe3ff53491d7bb705957826e4`

Verification commands:

```bash
sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz
tar -tzf artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz | head -n 30
```
