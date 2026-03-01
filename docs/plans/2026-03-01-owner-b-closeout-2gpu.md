# Owner B (GPU-1, Single-Writer) Closeout (2 GPU) — Finalization + Merge

> 角色定位：Owner B 是 report-pack / manifest / evidence tar 的**默认单写者**。任何更新 scoreboard/manifest/tar 的操作都在本分支完成并提交。

## Current status (已完成)

- ✅ `protocol_v1_convergecheck` 两条长训（dur0 + L4D=1e-4）与 3 个测试点 scoreboard（step 599/1999/4999）
- ✅ `protocol_v1_seg300_360` dur0 已补齐（`baseline_600_dur0` vs `planb_init_600_dur0`）并已更新 scoreboard
- ✅ DoD 资产指认页已落盘：`docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`
- ✅ Runbook：`docs/runbook/reproduce_code_freeze_2026-03-06.md`
- ✅ evidence tar 已重打并锁快照：
  - tar：`outputs/report_pack_2026-03-06_seg300dur0.tar.gz`
  - SHA：`docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`
  - manifest：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
  - `manifest_match: yes`
- ✅ Owner A 最终独立复核：PASS（manifest_match + DoD 播放性）

## Remaining work (现在要做什么)

### 0) （如未完成）合并 PR / 合入主分支（P0）

前置硬门控：
- `docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt` 指向 SoT tar（当前：`outputs/report_pack_2026-03-06_seg300dur0.tar.gz`）
- `manifest_match: yes`
- DoD 指针页无 TODO，且资产可播放/可打开

### 1) 最终自检（P0）

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
rg -n \"TODO_\" docs/report_pack/2026-02-27-v2/closeout_dod_assets.md || true
```

Expected: 无输出（DoD 指认页无 TODO）。

If Owner A reports `TODO_*` still exists:
- 说明 A 未同步到最新 `owner-b/closeout-2gpu`（版本偏斜），让 A 重新 `git fetch --all && git merge owner-b/closeout-2gpu` 后再复核。

### 2) 再次确认 manifest_match（P0）

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
cat docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt
TAR_PATH="$(awk '{print $2}' docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt)"
diff -u docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  <(tar -xOzf "$TAR_PATH" manifest_sha256.csv)
```

Expected: diff 为空。

### 3) 合并到主写作分支（P0）

目标：把 `owner-b/closeout-2gpu` 合入你们用于最终交付的主分支（或提 PR），确保写作仓库能直接引用：
- convergecheck/seg300_360 的 scoreboard 与结论 note
- DoD 指认页
- freeze runbook
- tar 的 SHA256 与 manifest 快照

合并前 hard gate：
- Owner A 的独立复核通过（manifest_match + DoD 播放性）
- `seg300_360` 的 dur0 证据已补齐并已重锁 evidence

PR / 同步：
- 若本地 `owner-b/closeout-2gpu` 比 `origin/owner-b/closeout-2gpu` 更新：`git push origin owner-b/closeout-2gpu`（更新 PR）

### 4) Stop rule（避免破坏证据链）

- 不要覆盖或删除旧 tar；只追加新的 tar（当前 SoT 以 `evidence_tar_sha256.txt` 为准）
- 不新增训练/扫参（除非写作上出现“缺一票否决证据”的新阻塞）
