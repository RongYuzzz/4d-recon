# Writing Mode v23 (Owner B / No-GPU): seg600_660 防守位接入 + 打包收口 + 口径清理

**Goal:** 在 Owner A 跑 `seg600_660` smoke200 的同时（GPU0），Owner B（No‑GPU）并行完成 v23 的“收口准备”，并在 A 交付后 **快速刷新 report-pack/evidence v23**，把新增 anti‑cherrypick 证据位与定性证据纳入写作链路。

**Non-goals / Constraints**
1. 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`）。
2. 不改协议、不改数据：`docs/protocols/protocol_v1.yaml` 不动；不触碰 canonical `data/selfcap_bar_8cam60f` 分布口径。
3. 不提交 `data/`、`outputs/`、`*.tar.gz`；仅提交 `scripts/`、`docs/`、`notes/`、`artifacts/report_packs/SHA256SUMS.txt`。
4. full600 预算为 0：不提出“补 full600”需求；如果必须新增 full600，需要新决议文件。

**Dependencies（来自 A，交付后才能做 v23 最终刷新）**
- A 将按 `docs/plans/2026-02-26-owner-a-planb-seg600-smoke200-and-handoff.md` 交付：
  - `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/{baseline_smoke200,planb_init_smoke200}/stats/test_step0199.json`
  - `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/{baseline_smoke200,planb_init_smoke200}/videos/traj_4d_step199.mp4`
  - `outputs/plan_b/selfcap_bar_8cam60f_seg600_660/velocity_stats.json`
  - `notes/anti_cherrypick_seg600_660.md`
  - `notes/handoff_planb_seg600_660_owner_a.md`
- 允许 fallback：若 A 因原始数据越界改跑 `seg300_360`，则依赖路径相应改为 `*_seg300_360`（本计划会在脚本侧兼容两者）。

---

## Task B81: 建立隔离 worktree + 预检对齐

**产出**
- 新增：`notes/owner_b_v23_preflight.md`

**Steps**
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260226-writing-mode-v23 origin/main
cd .worktrees/owner-b-20260226-writing-mode-v23
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

在 `notes/owner_b_v23_preflight.md` 记录：
- `git rev-parse HEAD`
- `git log -n 5 --oneline`
- 上述测试的 PASS 结论

---

## Task B82: 扩展 anti-cherrypick 汇总脚本（TDD）

**Why:** 当前 `scripts/summarize_planb_anticherrypick.py` 只覆盖 canonical/seg200_260/seg400_460；v23 需要额外纳入 `seg600_660`（或 fallback 的 `seg300_360`）。

**Code changes**
- Modify: `scripts/summarize_planb_anticherrypick.py`
  - 新增 group：`seg600_660`（匹配 `selfcap_bar_8cam60f_seg600_660`）
  - 兼容 fallback：`seg300_360`（匹配 `selfcap_bar_8cam60f_seg300_360`）
  - 输出规则：优先输出 `seg600_660`；若 metrics.csv 中缺失则输出 `seg300_360`；两者都缺失则输出 “(missing)” 行，但不崩溃。
- Modify: `scripts/tests/test_summarize_planb_anticherrypick.py`
  - 增加 dummy rows 覆盖 `seg600_660` smoke200（`baseline_smoke200` vs `planb_init_smoke200`）
  - 断言新增 section 中存在 `ΔPSNR/ΔLPIPS/ΔtLPIPS`

**Acceptance**
- `python3 scripts/tests/test_summarize_planb_anticherrypick.py` PASS

---

## Task B83: 定性证据入口补齐（seg600_660 或 fallback）

**Code/docs changes**
- Modify: `docs/execution/2026-02-26-planb-qualitative.md`
  - 增加一段 `seg600_660（smoke200）`（或 `seg300_360`）的 side-by-side 命令示例。

**Local-only assets（不入库）**
- 生成 side-by-side（等 A 产物到位后执行）：
```bash
cd /root/projects/4d-recon
bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/baseline_smoke200/videos/traj_4d_step199.mp4 \
  --right outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg600_660_step199.mp4 \
  --left_label baseline_seg600_660_smoke200 \
  --right_label planb_seg600_660_smoke200
```

**Note:** `pack_evidence.py` 已支持收录 `outputs/qualitative/planb_vs_baseline/*.mp4`，无需再改。

---

## Task B84: report-pack 文本口径清理（为 v23 做准备）

**Why:** 当前 `outputs/report_pack/{ablation_notes.md,failure_cases.md}` 的标题仍写 “v20”，容易在答辩/审计时引起质疑。v23 需要改为版本中性或 v23。

**Changes（写入仓库的目标是 v23 docs 快照，不直接提交 outputs/）**
- Modify (generated input before snapshot):
  - `outputs/report_pack/ablation_notes.md`
  - `outputs/report_pack/failure_cases.md`
  - 将标题从 “v20” 改为 “Writing Mode（2026-02-26）” 或 “v23”，并补充一行说明：v22 之后继续追加 seg600_660（或 fallback）防守位。

**Acceptance**
- v23 的 docs 快照中（见 B85）标题不再出现 “v20”。

---

## Task B85: 刷新 report-pack + evidence v23（依赖 A 产物到位）

**Precheck（依赖满足才继续）**
- 产物存在性（至少 stats/test + video）：
  - `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/baseline_smoke200/stats/test_step0199.json`
  - `outputs/protocol_v1_seg600_660/selfcap_bar_8cam60f_seg600_660/planb_init_smoke200/stats/test_step0199.json`

**Commands（以主仓 outputs 为源；允许在 worktree 执行，但需显式指定根）**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v23

python3 scripts/build_report_pack.py --outputs_root /root/projects/4d-recon/outputs
python3 scripts/summarize_scoreboard.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_anticherrypick.md
python3 scripts/analyze_smoke200_m1.py --metrics_csv /root/projects/4d-recon/outputs/report_pack/metrics.csv --out_md /root/projects/4d-recon/outputs/report_pack/planb_plus_weak_smoke200.md --baseline planb_init_smoke200

python3 scripts/pack_evidence.py \
  --repo_root /root/projects/4d-recon \
  --out_tar artifacts/report_packs/report_pack_2026-02-26-v23.tar.gz
```

**Docs 快照落盘（manifest 从 tar 解包）**
- New: `docs/report_pack/2026-02-26-v23/`
  - `metrics.csv`
  - `scoreboard.md`
  - `planb_anticherrypick.md`
  - `planb_plus_weak_smoke200.md`
  - `ablation_notes.md`
  - `failure_cases.md`
  - `manifest_sha256.csv`

**SHA 登记**
- Modify: `artifacts/report_packs/SHA256SUMS.txt`（追加 v23 行）

**Acceptance**
- v23 的 `planb_anticherrypick.md` 出现 `seg600_660`（或 fallback 的 `seg300_360`）小节与 delta。
- v23 `metrics.csv` 能 grep 到 `protocol_v1_seg600_660`（或 `seg300_360`）两条 test@199 行。
- `pack_evidence` tar 内包含新增 seg 的 `stats/test_step0199.json` 与 `videos/traj_4d_step199.mp4`（通过 `manifest_sha256.csv` 复核）。

---

## Task B86: 写作入口更新（不改结论，只扩防守）

**Changes**
- Modify: `notes/planb_verdict_writeup_owner_b.md`
  - 新增一段：seg600_660（或 seg300_360）smoke200 与 canonical/seg200_260/seg400_460 同向/反向的结论。
- Modify: `docs/writing/planb_paper_outline.md`
  - 在 anti‑cherrypick 防守位列表中加入 seg600_660（或 fallback）与 v23 证据链接。

**Acceptance**
- 写作骨架中的所有引用均指向 `docs/report_pack/2026-02-26-v23/*` 或 `notes/*`（不引用 worktree 绝对路径）。

---

## Task B87: 回归 + 合入 main

**Commands**
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v23
for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1
```

**Commit/Push（只提交 scripts/docs/notes/SHA256SUMS）**
```bash
git add -A
git commit -m "docs(report-pack): snapshot v23 incl seg600_660 anti-cherrypick and qualitative entry"
git push origin HEAD:main
```

