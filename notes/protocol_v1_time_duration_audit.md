# Protocol v1 Time/Duration Audit (Task 1.5, P0)

## Duration_reg target

- `duration_reg` target is taken from `cfg.init_duration` directly (`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:3694`).
- In `auto_init_duration=true` mode, trainer passes `init_duration=-1.0` into keyframe loader (`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1776-1791`), and the loader computes a positive local `init_duration` (`.../simple_trainer_freetime_4d_pure_relocation.py:1396-1401`).
- This auto-computed value is **not** written back to config (`cfg.init_duration`), and there is no config writeback path in trainer; `cfg.init_duration` remains the original value (commonly `-1`) when used by `duration_reg` target (`.../simple_trainer_freetime_4d_pure_relocation.py:3694`).
- Therefore, when `auto_init_duration=true` and `init_duration=-1`, the effective `duration_reg` target is `-1` (ambiguous/buggy relative to intended positive duration scale).
- Closeout policy: all decisive comparisons use `--lambda-duration-reg 0` (`dur0`) to avoid contaminating conclusions.
- Impacted new protocols (policy scope): `protocol_v1_calib`, `protocol_v1_convergecheck`, `protocol_v1_seg300_360`, `protocol_v2_final` (if run).

## Time normalization

Three active definitions are not fully aligned:

- Combine script: `total_frames = frame_end - frame_start + 1`, then `t_normalized = (keyframe - frame_start) / total_frames` (`third_party/FreeTimeGsVanilla/src/combine_frames_fast_keyframes.py:424,507`).
- Dataset parser: `total_frames = end_frame - start_frame`, then `time = (frame_idx - start_frame) / max(total_frames - 1, 1)` (`third_party/FreeTimeGsVanilla/datasets/FreeTime_dataset.py:723,765`).
- Trainer internals use mixed conventions: keyframe times use `(total_frames - 1)` while keyframe gap uses `total_frames` (`third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py:1385,1394`), and temporal-corr normalization also uses `(end-start-1)` (`.../simple_trainer_freetime_4d_pure_relocation.py:2800`).

Assessment:
- There is an inclusive/exclusive denominator mismatch risk (`+1`, `N`, `N-1` all appear), causing small but real temporal scale inconsistency.
- Closeout handling decision: treat as a known limitation for closeout (do not backwrite historical protocol evidence).
- If a code fix is required, it goes to a **new protocol only**; do not backwrite `protocol_v1`/`protocol_v2` evidence.

## Closeout decision

Decisive closeout comparisons use `dur0` (`--lambda-duration-reg 0`) because the current auto-duration path and duration regularization target are inconsistent when `init_duration=-1` in auto mode. Keeping duration regularization off in decisive comparisons removes this confounder, preserves auditability, and prevents evidence-chain contamination while we complete `protocol_v1_calib` and `protocol_v1_convergecheck`.
