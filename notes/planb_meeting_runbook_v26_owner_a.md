# Plan-B v26 Meeting Playback Runbook (Owner A)

- Date: 2026-02-26
- Scope: looped qualitative clips + playback fallback procedure
- Decision source: `docs/decisions/2026-02-26-planb-v26-freeze.md`
- Constraint reminder: this runbook does not introduce any new training or metric/protocol changes

## 1) Asset paths

### loop clip directory (preferred)

- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_step599_loop12s_h264.mp4`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg200_260_step599_loop12s_h264.mp4`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg400_460_step199_loop12s_h264.mp4`

### raw source fallback

- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`

### freeze-frame fallback

- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/planb_vs_baseline_step599_loop12s_h264_t6.jpg`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/planb_vs_baseline_seg200_260_step599_loop12s_h264_t6.jpg`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/planb_vs_baseline_seg400_460_step199_loop12s_h264_t6.jpg`

## 2) 30-second pre-meeting self-check

```bash
cd /root/projects/4d-recon

# raw mp4 existence
for p in \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4 \
; do
  test -f "$p" && echo "[OK] $p" || echo "[MISS] $p"
done

# loop clip probe
for p in \
  outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_step599_loop12s_h264.mp4 \
  outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg200_260_step599_loop12s_h264.mp4 \
  outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg400_460_step199_loop12s_h264.mp4 \
; do
  ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of default=nw=1 "$p"
done
```

Expected: three loop clips report around `duration=12.0` and `width=1280`.

## 3) Playback commands (recommended order)

Order: canonical -> seg200_260 -> seg400_460

### preferred (`ffplay`)

```bash
cd /root/projects/4d-recon
ffplay -autoexit outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_step599_loop12s_h264.mp4
ffplay -autoexit outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg200_260_step599_loop12s_h264.mp4
ffplay -autoexit outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg400_460_step199_loop12s_h264.mp4
```

### alternative (`mpv`)

```bash
cd /root/projects/4d-recon
mpv --force-window=yes outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_step599_loop12s_h264.mp4
mpv --force-window=yes outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg200_260_step599_loop12s_h264.mp4
mpv --force-window=yes outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg400_460_step199_loop12s_h264.mp4
```

## 4) Fallback procedure

1. If loop clip playback fails:
   - switch to freeze-frame covers in `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`
   - compare corresponding canonical/seg frames directly in slide viewer
2. If loop clip file is missing:
   - play raw source mp4 instead:
     - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
     - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
     - `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`

## 5) Owner B unblock pointer

- loop clips: `outputs/qualitative/planb_vs_baseline/clips_v26_looped/`
- covers: `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`
- this runbook note: `notes/planb_meeting_runbook_v26_owner_a.md`

