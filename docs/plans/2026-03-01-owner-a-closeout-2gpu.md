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
- `evidence_tar_sha256.txt` 指向最新 SoT tar（当前应为 `outputs/report_pack_2026-03-06_dodfix.tar.gz`）。

### 2) 独立复核 evidence tar（P0）

Source of truth：
- tar + SHA：`docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`
- manifest 快照：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon-owner-a
TAR_PATH="$(awk '{print $2}' docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt)"
diff -u docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt <(sha256sum "$TAR_PATH")
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  <(tar -xOzf "$TAR_PATH" manifest_sha256.csv)
```

Expected: diff 为空（`manifest_match: yes`）。

### 3) 独立复核 DoD 资产路径（P0）

Open:
- `docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`

Check:
- 3 个路径均存在，视频可播放，图可打开：
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

### 4) Stop rule（防止把 freeze 搞脏）

- 不要运行：`build_report_pack.py` / `summarize_scoreboard.py` / `pack_evidence.py`
- 除非 Owner B 明确要求补实验，否则不新增训练（包括 stage‑2）
