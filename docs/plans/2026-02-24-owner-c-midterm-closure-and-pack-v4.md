# Midterm Closure + Pack v4 Plan (Owner C, GPU2)

> 状态：Next。以 `docs/protocol.yaml` 为唯一真源；禁止私改帧段/相机 split/关键超参（若必须改，先版本升级协议并重跑 baseline）。

**Goal:** 在 protocol v1 下把 midterm “可复现闭环”一次性做完：
- Baseline 600 / Ours-Weak 600 / Control(NoCue) 600：视频 + `val/test` stats（test 含 `tlpips`）
- `outputs/report_pack/metrics.csv` 更新（含 `stage`、`tlpips`）
- evidence tarball v4：包含 `manifest_sha256.csv` + `git_rev.txt`，并更新 `artifacts/report_packs/SHA256SUMS.txt`

**Parallel Safety:** 只跑实验、更新材料、打包；不改 trainer/数据入口脚本；不把 `data/` 与 `outputs/` 入库。

**Default Resources:** `GPU2`。

---

## Task C20: Sanity（protocol + data）

Run:
```bash
cd /root/projects/4d-recon
ls -la docs/protocol.yaml docs/protocols/protocol_v1.yaml
test -d data/selfcap_bar_8cam60f/triangulation
```

Expected:
- `docs/protocol.yaml` 指向 v1（单一真源）
- `data/selfcap_bar_8cam60f/triangulation` 存在（60 帧）

---

## Task C21: Baseline 600（GPU2, protocol v1）

Run:
```bash
cd /root/projects/4d-recon
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600 \
bash scripts/run_train_baseline_selfcap.sh
```

Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/stats/val_step0599.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/baseline_600/stats/test_step0599.json`（应含 `tlpips`）

---

## Task C22: Control 600（weak 路径但无 cue）

Run:
```bash
cd /root/projects/4d-recon
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600 \
bash scripts/run_train_control_weak_nocue_selfcap.sh
```

Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/control_weak_nocue_600/stats/test_step0599.json`（应含 `tlpips`）

---

## Task C23: Ours-Weak 600（等 A 给 tuned 参数；无则先用占位）

说明：
- 等 Owner A 给出最终的 `PSEUDO_MASK_WEIGHT` / `PSEUDO_MASK_END_STEP`（以及 cue backend/tag）。
- 若 A 尚未给定版参数：先用占位（diff backend + `end_step=200`）跑出闭环，后续可覆盖重跑。

Run（示例，占位参数）：
```bash
cd /root/projects/4d-recon
GPU=2 RESULT_DIR=outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600 \
CUE_TAG=selfcap_bar_8cam60f_v1 CUE_BACKEND=diff MASK_DOWNSCALE=4 \
PSEUDO_MASK_WEIGHT=0.2 PSEUDO_MASK_END_STEP=200 \
bash scripts/run_train_ours_weak_selfcap.sh
```

Expected:
- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/ours_weak_600/stats/test_step0599.json`（应含 `tlpips`）

---

## Task C24: 刷新 report-pack（metrics.csv）

Run:
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
```

Expected:
- `outputs/report_pack/metrics.csv` 至少包含三组 run 的 `val/test` 两类行
- `metrics.csv` 的 test 行包含 `tlpips`（非空）

---

## Task C25: 生成 evidence tarball v4 + 更新 SHA256SUMS

Run:
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
OUT=artifacts/report_packs/report_pack_$(date +%F)-v4.tar.gz
$PY scripts/pack_evidence.py --repo_root . --out_tar "$OUT"
sha256sum "$OUT" >> artifacts/report_packs/SHA256SUMS.txt
tail -n 5 artifacts/report_packs/SHA256SUMS.txt
```

Expected:
- tar 内包含：`manifest_sha256.csv`、`git_rev.txt`、`outputs/report_pack/metrics.csv`、以及三条 run 的 `stats/*.json` 与 `videos/*.mp4`

