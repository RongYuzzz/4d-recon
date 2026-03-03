# Repository Guidelines

## Project Structure & Module Organization

- `scripts/`: runnable experiment entrypoints (Bash + Python). Naming patterns: `run_*.sh`, `viz_*.py`.
- `scripts/tests/`: `pytest` contract tests for runners/diagnostics/packaging.
- `third_party/FreeTimeGsVanilla/`: forked training code used by protocol runners.
- `docs/`: protocols (`docs/protocol.yaml`, `docs/protocols/`), report packs, plans (project closeout: `docs/plans/2026-03-01-project-closeout-plan.md`), reviews (discussion brief: `docs/reviews/2026-02-28/mentor-discussion-brief.md`).
- `notes/`: experiment notes, audit trails, interpretation writeups.
- `data/`: adapted datasets/scenes (commonly expects `images/`, `triangulation/`, `sparse/`).
- `outputs/`: run artifacts (configs, stats JSON, ckpts, videos, report packs). Treat as append-only; don’t hand-edit.

## Build, Test, and Development Commands

- Run tests: `pytest -q` (or targeted: `pytest -q scripts/tests/test_*.py`).
- Train (SelfCap canonical):
  - Baseline: `bash scripts/run_train_baseline_selfcap.sh [result_dir]`
  - Plan-B init: `bash scripts/run_train_planb_init_selfcap.sh [result_dir]`
  - Stage-2 runner: `bash scripts/run_train_planb_feature_loss_v2_selfcap.sh [result_dir]`
- Update metrics + tables: `python3 scripts/build_report_pack.py` then run `python3 scripts/summarize_scoreboard.py ...`.
- Package evidence tarball: `python3 scripts/pack_evidence.py --out_tar outputs/report_pack_YYYY-MM-DD.tar.gz`.
- Data adapters (when a scene lacks `triangulation/`): see `scripts/export_triangulation_from_colmap_sparse.py` and `scripts/adapt_selfcap_release_to_freetime.py`.

Tip: most runners honor `VENV_PYTHON=/path/to/python` to point at the FreeTimeGsVanilla virtualenv.

## Coding Style & Naming Conventions

- Python: 4-space indentation; keep edits small and audit-friendly; prefer explicit flags/paths over hidden defaults.
- Bash: start with `set -euo pipefail`; expose knobs via env vars (`FOO="${FOO:-default}"`); print key settings at start.
- Protocols: versioned YAMLs live in `docs/protocols/protocol_v*.yaml`; update `docs/protocol.yaml` only when intentionally changing the active protocol.

## Testing Guidelines

- Framework: `pytest`.
- For new scripts that affect audit/packaging/diagnostics, add a contract test in `scripts/tests/` asserting required files/keys exist and outputs are deterministic.

## Commit & Pull Request Guidelines

- Commit messages follow Conventional Commits with scopes, e.g. `feat(diagnostics): ...`, `docs(report-pack): ...`, `chore(meeting): ...`.
- PRs must include: protocol file(s), exact command(s), `result_dir` paths, verification (`pytest ...`, and for releases `manifest_match: yes` via the tarball manifest).
- Do not rewrite historical results; add new protocol versions and write new output directories instead.
