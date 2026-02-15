# T0 Gradient Check Log

## Scope
- Target params: `velocities`, `durations`
- Source: trainer runtime log + optional CSV (`T0_GRAD_LOG_PATH`)
- PASS rule (from plan): gradients mostly non-zero and finite.

## How to run
```bash
bash /root/projects/4d-recon/scripts/run_t0_zero_velocity.sh \
  <triangulation_input_dir> \
  <colmap_data_dir> \
  /root/projects/4d-recon/outputs/t0_zero_velocity
```

## Output files
- Baseline grad log: `outputs/t0_zero_velocity/baseline/t0_grad.csv`
- Zero-velocity grad log: `outputs/t0_zero_velocity/zero_velocity/t0_grad.csv`

## Status (`2026-02-15`)
- Environment setup completed.
- Dataset path pending (`triangulation + COLMAP` not found locally).
- Numeric PASS/FAIL to be filled after first successful run.

## Result Summary (to fill)
- Baseline: `PENDING`
- Zero-velocity: `PENDING`
- Conclusion: `PENDING`

## Notes
- Trainer now prints per-interval T0 diagnostics:
  - `t_range`
  - `|v| min/mean/max`
  - `|dx| min/mean/max`
  - `||grad_v||`, `||grad_duration||`
