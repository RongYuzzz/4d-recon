# Meeting Checklist v26 (2-minute Preflight)

## 1) 入口（点击顺序）
- 先开 `docs/reviews/2026-02-26/meeting-index-v26.md`，确认本次入口是 v26。
- 再开 `docs/reviews/2026-02-26/meeting-handout-v26.md`，按 handout 的结论 -> 数字 -> 证据顺序讲。
- 若临场需要回溯，只从 index 跳转，不临时拼接其他版本文档。

## 2) 冻结纪律（N=0）
- 本轮纪律写死：新增 full600 预算 `N=0`，不新增 smoke200/full600。
- 会前再次对齐决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`。
- 禁止运行任何 `run_train_*.sh`，仅允许 docs/notes 入口整理与引用接线。

## 3) 数字真源（v26 report-pack 四件套）
- 在仓库根目录执行：
```bash
for p in \
  docs/report_pack/2026-02-26-v26/metrics.csv \
  docs/report_pack/2026-02-26-v26/scoreboard.md \
  docs/report_pack/2026-02-26-v26/planb_anticherrypick.md \
  docs/report_pack/2026-02-26-v26/manifest_sha256.csv; do
  test -f "$p" && echo "[OK] $p" || echo "[MISS] $p"
done
```

## 4) evidence tar SHA（rg + sha256sum）
- 会前核对离线证据包：
```bash
rg -n "report_pack_2026-02-26-v26.tar.gz" artifacts/report_packs/SHA256SUMS.txt
expected=$(rg "report_pack_2026-02-26-v26.tar.gz" artifacts/report_packs/SHA256SUMS.txt | awk '{print $1}')
actual=$(sha256sum artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz | awk '{print $1}')
test "$expected" = "$actual" && echo "[OK] tar SHA match" || echo "[MISMATCH] tar SHA"
```

## 5) 视频资产自检（loop12s 优先）
- 先按 runbook：`notes/planb_meeting_runbook_v26_owner_a.md` 做 30 秒自检。
- 优先检查 `outputs/qualitative/planb_vs_baseline/clips_v26_looped/` 下三条 loop12s 片段可播放。
- 复用 runbook 中 `ffprobe`/`ffplay`（或 `mpv`）命令，不现场改播放资产。

## 6) 兜底策略（只记路径与原则）
- 原则：loop12s 失败时先 freeze-frame，再退 raw mp4。
- freeze-frame 路径：`outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`。
- raw mp4 路径：`outputs/qualitative/planb_vs_baseline/` 下 canonical/seg 对应三条源视频。

## 7) 禁止项（会前最后口头确认）
- 不要现场跑实验，不要启动任何训练任务。
- 不要生成新的 report-pack vXX，不要改数字口径与协议定义。
- 只引用 v26 现有证据链与已登记 SHA，避免临场新增“新结果”。

## Optional) Offline Bundle Check（local-only）
- 若本地存在 bundle，则执行：`sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`。
- 路径：`artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`（仅本地物料，不入库）。
- SHA 真源：`notes/planb_meeting_assets_v26_owner_a.md`。
