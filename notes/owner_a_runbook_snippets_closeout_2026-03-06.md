# Owner A Runbook Snippets (Closeout 2026-03-06)

Source:
- `/root/autodl-tmp/projects/4d-recon-owner-a/notes/planb_meeting_runbook_v26_owner_a.md`

## Asset pointer snippets

- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`

## Playback/fallback snippets

```bash
# Preferred looped clips
ffplay -autoexit outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_step599_loop12s_h264.mp4

# Fallback raw clip
ffplay -autoexit outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4
```

These snippets are ingested to keep Owner A's qualitative asset workflow in the final closeout runbook.
