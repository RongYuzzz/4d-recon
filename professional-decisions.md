<!--
This file is intentionally citation-free.
If you need to justify a decision, link to an internal repo document path instead of pasting tool citations.
-->

# Professional Decisions (for 2026-03-06 Code Freeze)

- Version: v1.1
- Date: 2026-03-01
- Scope: closeout decisions that are **non-negotiable** for the 2026-03-06 freeze
- Execution plan: `docs/plans/2026-03-01-project-closeout-plan.md`
- Mentor brief (execution SoT): `docs/reviews/2026-02-28/mentor-discussion-brief.md`

## 0. One-page decisions (lock first, then execute)

### D0: Baseline is not “paper FreeTimeGS reproduction”

- We do **not** claim end-to-end reproduction of FreeTimeGS (e.g., ROMA init, dynamic-region eval).
- Our baseline is explicitly: **protocolized FreeTimeGsVanilla fork** on **SelfCap bar (8 cams × 60 frames)** with **fixed camera split** and our audited runner/packaging stack.
- Any new experiment that changes behavior/eval MUST go to **new protocol + new output dir** (no backwrite to `protocol_v1/v2` evidence chain).

### D1: Baseline hardening must close 3 P0 attack surfaces

**Must do (minimal-change, high leverage):**

1) `lambda_4d_reg` calibration (smoke200 sweep)
- Sweep: `1e-4 / 1e-3 / 1e-2` on SelfCap canonical (smoke200).
- Output: one short note + one scoreboard table that pins the “calibrated baseline recipe”.

2) `duration_reg` target ambiguity/bug: fix-or-disable (but must be auditable)
- If `auto_init_duration=true` with `init_duration=-1` makes the duration-reg target ill-defined, we do **not** allow decisive comparisons to be contaminated.
- Allowed options:
  - Fix semantics **in a new protocol only** and document the change; OR
  - Disable for all decisive comparisons: `--lambda-duration-reg 0` (recommended for speed/defensibility if fix is risky).

3) Time-normalization / off-by-one audit: fix-or-limitation (new protocol only)
- Audit combine/dataset/trainer consistency.
- Either fix in new protocol and rerun only the new-protocol experiments, or clearly mark as limitation and avoid paper-level claims that depend on that timing.

### D2: 600-step results cannot be the only support (must run convergecheck)

- Run a **convergence sanity check**: `baseline` vs `planb_init` long training.
- Minimum: `MAX_STEPS=5000` with multi-step eval/save at `600,2000,5000` (10k optional if budget permits).
- The conclusion MUST be written in one of three branches and reflected in claims:
  - A) gap persists/expands → not just early efficiency;
  - B) gap closes → claim becomes “training efficiency / robustness (anytime)”;
  - C) gap reverses → stop and write a limitation/failure boundary.

### D3: Stage-2 is closed (no more sweeps), but allow 1 “final decay” attempt

- No more full600 hyperparam sweeping.
- Allow **at most 1–2 runs** for “feature-loss decay schedule”:
  - optional smoke200 trend check;
  - then one full600 run only if smoke200 trend is promising.
- Success criterion (must be explicit in the note):
  - vs `planb_init_600`: **tLPIPS improves** and **LPIPS does not regress**, beyond the smoke200 noise band.
- If still trade-off/mixed trend: stop; write a failure analysis with minimal mechanism evidence.

### D4: Anti-cherry-pick / generalization must add a second segment/scene

- Minimum deliverable: one additional segment/scene with `baseline_600` vs `planb_init_600`.
- Output requirement: **one line of metrics + one qualitative video** (even if negative, it becomes a boundary).

### D5: Engineering audit gate is mandatory (`manifest_match: yes`)

- Evidence tar must include `git_rev.txt` and `manifest_sha256.csv`.
- `docs/report_pack/2026-02-27-v2/manifest_sha256.csv` must match the tar’s `manifest_sha256.csv`.
- The final tar filename + SHA256 must be recorded in `docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`.

### D6: DoD for 2026-03-06 freeze (must be “pointable”)

**Content 3-piece set**
- One main scoreboard entry point (explicit protocol + step).
- One qualitative video asset (static/dynamic split or equivalent editability demo).
- One explanatory figure (trade-off / failure boundary / Pareto).

**Audit 3-piece set**
- One evidence tarball (sha256 locked) + `manifest_match: yes`.
- One runbook that reproduces the freeze artifacts end-to-end.

## 1. Execution constraints (discipline)

- Do not “fix” old results by overwriting outputs; add new outputs under:
  - `outputs/protocol_v1_calib/`
  - `outputs/protocol_v1_convergecheck/`
  - `outputs/protocol_v1_seg300_360/` (or chosen second scene)
  - `outputs/protocol_v2_final/`
- Every new run must produce: `cfg.yml` + `stats/test_step*.json` + `throughput.json`.
- Daily: rebuild `outputs/report_pack/metrics.csv`, append-only scoreboard updates, no deletions.

## 2. Resource allocation (default 3人3GPU; downgrade allowed)

- GPU-0: baseline calibration + convergecheck (long runs)
- GPU-1: second segment/scene (anti-cherry-pick)
- GPU-2 (+ CPU): manifest/audit packaging + stage-2 final decay attempt

If only 2 GPUs are available, prioritize D1 + D2 + D5; run D4 next; D3 only if time remains.

