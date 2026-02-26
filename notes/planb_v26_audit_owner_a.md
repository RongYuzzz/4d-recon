# Plan-B v26 Audit (Owner A)

- Date: 2026-02-26
- Scope: A131 quick audit (No-GPU, no new training)
- Decision source: `docs/decisions/2026-02-26-planb-v26-freeze.md`

## Step 1: v26 report-pack snapshot files

- Command: `ls -la docs/report_pack/2026-02-26-v26/{metrics.csv,scoreboard.md,planb_anticherrypick.md,manifest_sha256.csv}`
- Result: PASS
- Key lines:
  - `metrics.csv` present
  - `scoreboard.md` present
  - `planb_anticherrypick.md` present
  - `manifest_sha256.csv` present

## Step 2: evidence tar checksum verification

- Command:
  - `rg -n "report_pack_2026-02-26-v26" artifacts/report_packs/SHA256SUMS.txt`
  - `sha256sum /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`
- Result: PASS
- Key lines:
  - Registered SHA (`SHA256SUMS.txt`): `43e04974f95d4628c02cc7b65e5fbf44db4fd82329e306ec082a57dd90102536`
  - Actual SHA (`sha256sum`): `43e04974f95d4628c02cc7b65e5fbf44db4fd82329e306ec082a57dd90102536`

## Step 3: rebuild report_pack from outputs and summarize

- Command:
  - `python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs --out_dir /root/projects/4d-recon/outputs/report_pack`
  - `python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md`
  - `python3 scripts/summarize_planb_anticherrypick.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md`
- Result: PASS
- Key lines:
  - `wrote /root/projects/4d-recon/outputs/report_pack/metrics.csv (101 rows)`
  - `wrote /root/projects/4d-recon/outputs/report_pack/scoreboard.md (10 runs)`
  - `wrote /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md`

## Acceptance checks

- Required sections exist in rebuilt anti-cherrypick markdown:
  - `seg300_360` present
  - `seg400_460` present
  - `seg1800_1860` present
- Snapshot consistency:
  - `diff -u docs/report_pack/2026-02-26-v26/planb_anticherrypick.md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md` -> no diff
- Verdict: PASS

