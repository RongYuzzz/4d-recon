# Reproduce Code Freeze 2026-03-06

## Scope

This runbook reproduces the closeout evidence chain for:
- `protocol_v1_convergecheck` (baseline vs planb_init at steps 599/1999/4999)
- `protocol_v1_seg300_360` (`*_dur0`, baseline vs planb_init at step 599)
- freeze packaging (`report_pack_2026-03-06_seg300dur0.tar.gz` + manifest snapshot lock)

Integrated inputs from Owner A:
- `notes/protocol_v1_time_duration_audit.md`
- `notes/owner_a_runbook_snippets_closeout_2026-03-06.md`

## Locked settings

- `seed=42`
- `lambda_duration_reg=0` (dur0)
- `lambda_4d_reg=1e-4` (L4D)
- camera split: train `02,03,04,05,06,07`, val `08`, test `09`

## 1) Convergecheck runs (5k)

Note: these two runs can be executed in parallel on 2 GPUs (recommended), or sequentially on 1 GPU by changing `GPU=<id>`.

### baseline_long5k_dur0

```bash
cd /root/autodl-tmp/projects/4d-recon
GPU=0 MAX_STEPS=5000 \
RESULT_DIR=outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/baseline_long5k_dur0 \
EVAL_STEPS=600,2000,5000 SAVE_STEPS=600,2000,5000 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg 1e-4" \
bash scripts/run_train_baseline_selfcap.sh
```

### planb_init_long5k_dur0

```bash
cd /root/autodl-tmp/projects/4d-recon
GPU=1 MAX_STEPS=5000 \
RESULT_DIR=outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/planb_init_long5k_dur0 \
PLANB_OUT_DIR=outputs/plan_b/selfcap_bar_8cam60f_convergecheck_long5k_dur0 \
EVAL_STEPS=600,2000,5000 SAVE_STEPS=600,2000,5000 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg 1e-4" \
bash scripts/run_train_planb_init_selfcap.sh
```

Quick self-check (`cfg.yml` must be dur0):
```bash
cd /root/autodl-tmp/projects/4d-recon
rg -n "lambda_(duration_reg|4d_reg)" \
  outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/planb_init_long5k_dur0/cfg.yml
```

## 2) seg300_360 runs (600)

### baseline_600_dur0

```bash
cd /root/autodl-tmp/projects/4d-recon
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 GPU=1 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600_dur0 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg 1e-4" \
bash scripts/run_train_baseline_selfcap.sh
```

### planb_init_600_dur0

```bash
cd /root/autodl-tmp/projects/4d-recon
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 GPU=1 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600_dur0 \
BASELINE_INIT_NPZ=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600_dur0/keyframes_60frames_step5.npz \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg 1e-4" \
bash scripts/run_train_planb_init_selfcap.sh
```

Quick self-check (`cfg.yml` and `test_step0599.json`):
```bash
cd /root/autodl-tmp/projects/4d-recon
for d in \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600_dur0 \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600_dur0; do \
  echo "--- $d"; \
  rg -n "lambda_(duration_reg|4d_reg)" "$d/cfg.yml"; \
  ls -la "$d/stats/test_step0599.json"; \
done
```

## 3) Build scoreboards

```bash
cd /root/autodl-tmp/projects/4d-recon
python3 scripts/build_report_pack.py

python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_convergecheck/ \
  --stage test --step 599 --baseline_regex "^baseline_long5k_dur0$"

python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck_step2000.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_convergecheck/ \
  --stage test --step 1999 --baseline_regex "^baseline_long5k_dur0$"

python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_protocol_v1_convergecheck_step5000.md \
  --select_contains selfcap_bar_8cam60f \
  --select_prefix outputs/protocol_v1_convergecheck/ \
  --stage test --step 4999 --baseline_regex "^baseline_long5k_dur0$"

python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_seg300_360_full600.md \
  --select_contains _dur0 \
  --select_prefix outputs/protocol_v1_seg300_360/ \
  --stage test --step 599 \
  --baseline_regex "^baseline_600_dur0$"

python3 scripts/summarize_scoreboard.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md docs/report_pack/2026-02-27-v2/scoreboard_code_freeze_2026-03-06.md \
  --protocol_id code_freeze_2026-03-06 \
  --select_contains selfcap_bar_8cam60f/ \
  --select_prefix "" \
  --stage test --step 599
```

## 3.5) Generate the DoD explanatory figure (optional but recommended)

```bash
cd /root/autodl-tmp/projects/4d-recon
python3 scripts/viz_convergecheck_v1_psnr_tlpips.py \
  --baseline_dir outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/baseline_long5k_dur0 \
  --planb_dir outputs/protocol_v1_convergecheck/selfcap_bar_8cam60f/planb_init_long5k_dur0 \
  --out_png outputs/report_pack/diagnostics/closeout_20260306/convergecheck_v1_psnr_tlpips_vs_step.png
```

## 4) Freeze package + manifest lock

```bash
cd /root/autodl-tmp/projects/4d-recon
python3 scripts/build_report_pack.py
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-03-06_seg300dur0.tar.gz

# lock snapshot to tar manifest (source of truth)
tar -xOzf outputs/report_pack_2026-03-06_seg300dur0.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
sha256sum outputs/report_pack_2026-03-06_seg300dur0.tar.gz | tee docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt

# hard gate
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  <(tar -xOzf outputs/report_pack_2026-03-06_seg300dur0.tar.gz manifest_sha256.csv)
```

Expected: final `diff` is empty (`manifest_match: yes`).
