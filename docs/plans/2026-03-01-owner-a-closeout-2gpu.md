# Owner A (GPU-0) Closeout (2 GPU) — Post-freeze Checklist

> 角色定位：Owner A 不写 report-pack / manifest / evidence tar（单写者是 Owner B）。Owner A 只做训练落盘、审计 note、以及最后的独立复核。

## Current status (已完成)

- ✅ Task 1.5：`notes/protocol_v1_time_duration_audit.md`（dur0 依据）
- ✅ smoke200 校准（含 `l4d=1e-4`）
- ✅ `protocol_v1_convergecheck` baseline 长训：`outputs/.../baseline_long5k_dur0`（dur0 + L4D=1e-4）
- ✅ 误配 run 已隔离到 `_aborted_*` 目录（不参与对比）
- ✅ Runbook 片段已交付并被 Owner B 集成到 freeze runbook

## Remaining work (现在要做什么)

### 1) 同步到 freeze 分支（只读/复核用）

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon-owner-a
git fetch --all
git merge owner-b/closeout-2gpu
```

Sanity check (anti version-skew):
```bash
ls -la docs/report_pack/2026-02-27-v2/closeout_dod_assets.md
rg -n "TODO_" docs/report_pack/2026-02-27-v2/closeout_dod_assets.md || true
cat docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt
```

Expected:
- `closeout_dod_assets.md` 不包含 `TODO_`。
- `evidence_tar_sha256.txt` 指向最新 SoT tar（以文件内容为准；当前为 `outputs/report_pack_2026-03-06_seg300dur0.tar.gz`）。

### 2) （如缺失）补齐 `seg300_360` 的 dur0 证据（P0，GPU 任务）

如果以下两条目录已存在且 `cfg.yml` 中 `lambda_duration_reg: 0.0`，可跳过本节：
- `.../baseline_600_dur0`
- `.../planb_init_600_dur0`

依据：`notes/protocol_v1_time_duration_audit.md` 明确要求 `protocol_v1_seg300_360` 也必须 `dur0`（否则 duration_reg 目标值会被 `init_duration=-1` 的 auto-init 路径污染）。

先自检现有 evidence 是否已是 dur0：
```bash
cd /root/autodl-tmp/projects/4d-recon-owner-a
for d in \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600 \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600; do \
  echo "--- $d"; \
  rg -n "lambda_(duration_reg|4d_reg)" "$d/cfg.yml" || true; \
done
```

如果看到 `lambda_duration_reg: 0.001`（当前就是这样），则按 append-only 原则**不要覆盖旧目录**，新增两条 dur0 runs：

```bash
cd /root/autodl-tmp/projects/4d-recon-owner-a

# baseline_600_dur0
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 \
GPU=0 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600_dur0 \
EVAL_STEPS=600 SAVE_STEPS=600 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg 1e-4" \
bash scripts/run_train_baseline_selfcap.sh

# planb_init_600_dur0
DATA_DIR=data/selfcap_bar_8cam60f_seg300_360 \
GPU=0 MAX_STEPS=600 \
RESULT_DIR=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600_dur0 \
BASELINE_INIT_NPZ=outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600_dur0/keyframes_60frames_step5.npz \
EVAL_STEPS=600 SAVE_STEPS=600 \
EXTRA_TRAIN_ARGS="--lambda-duration-reg 0 --lambda-4d-reg 1e-4" \
bash scripts/run_train_planb_init_selfcap.sh
```

完成后本地自检（最小可审计产物 + dur0）：
```bash
cd /root/autodl-tmp/projects/4d-recon-owner-a
for d in \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600_dur0 \
  outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600_dur0; do \
  echo \"--- $d\"; \
  rg -n \"lambda_(duration_reg|4d_reg)\" \"$d/cfg.yml\"; \
  ls -la \"$d/stats/test_step0599.json\"; \
done
```

交付给 Owner B（只发路径 + 自检结果；不要更新 report-pack/manifest/tar）：
- `baseline_600_dur0` 路径
- `planb_init_600_dur0` 路径
- 两个 `cfg.yml` 中 `lambda_duration_reg: 0.0` 的行号截图/粘贴

### 3) 独立复核 evidence tar（P0）

Source of truth：
- tar + SHA：`docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`
- manifest 快照：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

注意：如果 Owner B 因 seg300_360 dur0 补齐而**重打 tar 并重锁快照**，则本步骤应以 `evidence_tar_sha256.txt` 的最新内容为准（避免对旧 tar 做无意义复核）。

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon-owner-a
TAR_PATH="$(awk '{print $2}' docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt)"
diff -u docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt <(sha256sum "$TAR_PATH")
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  <(tar -xOzf "$TAR_PATH" manifest_sha256.csv)
```

Expected: diff 为空（`manifest_match: yes`）。

### 4) 独立复核 DoD 资产路径（P0）

Open:
- `docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`

Check:
- 4 个路径均存在，视频可播放，图可打开：
  - static video
  - dynamic video
  - side-by-side compare
  - explanatory figure (`.png`)

Minimal playback (copy paths from DoD pointer page):
```bash
ffplay -autoexit <STATIC_MP4>
ffplay -autoexit <DYNAMIC_MP4>
ffplay -autoexit <SIDE_BY_SIDE_MP4>
python3 - <<'PY'
from PIL import Image
Image.open("<EXPLANATORY_PNG>").verify()
print("png_ok")
PY
```

### 5) Stop rule（防止把 freeze 搞脏）

- 不要运行：`build_report_pack.py` / `summarize_scoreboard.py` / `pack_evidence.py`
- 除非 Owner B 明确要求补实验，否则不新增训练（包括 stage‑2）
