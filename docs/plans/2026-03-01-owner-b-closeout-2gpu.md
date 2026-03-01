# Owner B (GPU-1, Single-Writer) Closeout (2 GPU) — Finalization + Merge

> 角色定位：Owner B 是 report-pack / manifest / evidence tar 的**默认单写者**。任何更新 scoreboard/manifest/tar 的操作都在本分支完成并提交。

## Current status (已完成)

- ✅ `protocol_v1_convergecheck` 两条长训（dur0 + L4D=1e-4）与 3 个测试点 scoreboard（step 599/1999/4999）
- ⚠️ `protocol_v1_seg300_360` 需要 dur0 补齐（见 Remaining work #0）
- ✅ DoD 资产指认页已落盘：`docs/report_pack/2026-02-27-v2/closeout_dod_assets.md`
- ✅ Runbook：`docs/runbook/reproduce_code_freeze_2026-03-06.md`
- ✅ evidence tar 已重打并锁快照：
  - tar：`outputs/report_pack_2026-03-06_dodfix.tar.gz`
  - SHA：`docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`
  - manifest：`docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
  - `manifest_match: yes`

## Remaining work (现在要做什么)

### 0) BLOCKER：补齐 `seg300_360` 的 dur0 证据并重锁 evidence（P0）

依据：`notes/protocol_v1_time_duration_audit.md` 已把 `protocol_v1_seg300_360` 纳入 `dur0` policy scope。

当前 evidence 目录：
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/baseline_600/cfg.yml` → `lambda_duration_reg: 0.001`
- `outputs/protocol_v1_seg300_360/selfcap_bar_8cam60f_seg300_360/planb_init_600/cfg.yml` → `lambda_duration_reg: 0.001`

处理原则（append-only）：
- 不覆盖旧目录（保留为历史参考）
- 新增 `baseline_600_dur0` / `planb_init_600_dur0`

执行分工（推荐）：
- Owner A（GPU）负责跑 `baseline_600_dur0` + `planb_init_600_dur0` 并自检 `cfg.yml: lambda_duration_reg: 0.0` 与 `stats/test_step0599.json` 存在
- Owner B（单写者）负责更新 docs/report-pack + 重新打包 evidence tar + 重锁 manifest/SHA

Owner B 接收 Owner A 产物后，按顺序做：
1. 自检两条新 runs：
   - `cfg.yml` 中 `lambda_duration_reg: 0.0`，`lambda_4d_reg: 0.0001`
   - `stats/test_step0599.json` 存在
2. 重新生成并提交 `seg300_360` 的 scoreboard（避免继续引用 durreg=1e-3 的旧 runs）：
   - 目标文件：`docs/report_pack/2026-02-27-v2/scoreboard_seg300_360_full600.md`
3. 更新并提交 freeze runbook：
   - `docs/runbook/reproduce_code_freeze_2026-03-06.md` 的 seg300_360 section 指向 `*_dur0` 目录
4. 重打 evidence tar（新文件名，保持 append-only），并重锁：
   - 更新 `docs/report_pack/2026-02-27-v2/evidence_tar_sha256.txt`
   - 更新 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`
   - hard gate：确保 `manifest_match: yes`
5. 通知 Owner A：按其 checklist 的 “独立复核 evidence tar (P0)” 重新跑一遍（以最新 `evidence_tar_sha256.txt` 为准）

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
- `seg300_360` 的 dur0 证据已补齐并已重锁 evidence（见 #0）

PR / 同步：
- 若本地 `owner-b/closeout-2gpu` 比 `origin/owner-b/closeout-2gpu` 更新：`git push origin owner-b/closeout-2gpu`（更新 PR）

### 4) Stop rule（避免破坏证据链）

- 不要覆盖或删除旧 tar；只追加新的 tar（当前 SoT 以 `evidence_tar_sha256.txt` 为准）
- 不新增训练/扫参（除非写作上出现“缺一票否决证据”的新阻塞）
