# Owner B 后续计划：Writing Mode（v26 冻结期）会议 Handout + Claim 审计（No‑GPU）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner B（No‑GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

在不使用 GPU、不新增训练、不改 `protocol_v1` 与训练数值逻辑的前提下：

1. 产出**可直接发给导师/同行**的单文件会议材料（Handout），避免会前“入口散落”。
2. 对现有写作材料做一次“Claim 审计”，确保不会被消融/口径/范围声明反噬（尤其是 Mutual NN 叙事与绝对 PSNR 攻击面）。
3. 在 Owner A 生成会议 clip 清单后，把引用入口接线到 handout 与 onepager（不引入新版本号、不新打 report-pack）。

## 1) 约束（必须遵守）

- 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`），不新增 smoke200/full600。
- 不改协议：不改 `docs/protocols/protocol_v1.yaml`；不改训练数值逻辑。
- 不入库大文件：`data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 会中数字引用口径：只允许引用 v26 report-pack 快照：
  - `docs/report_pack/2026-02-26-v26/metrics.csv`
  - `docs/report_pack/2026-02-26-v26/scoreboard.md`
  - `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
  - `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`

## 2) 输入依赖（不阻塞推进）

已在 `origin/main` 的写作材料（现状）：

- `docs/writing/planb_onepager_v26.md`
- `docs/writing/planb_talk_outline_v26.md`
- `docs/writing/planb_qa_cards_v26.md`
- `docs/writing/planb_paper_outline.md`
- `notes/planb_verdict_writeup_owner_b.md`
- Owner A 资产 notes：
  - `notes/planb_v26_audit_owner_a.md`
  - `notes/planb_table1_v26_owner_a.md`
  - `notes/planb_qualitative_frames_v26_owner_a.md`
  - `notes/handoff_planb_v26_assets_owner_a.md`

Owner A 可能新增（并行产出，若到位则接线；不到位不阻塞）：

- `notes/planb_meeting_assets_v26_owner_a.md`（clips/frames 清单与播放顺序）

## 3) 任务分解（B151–B155）

### B151. 隔离 worktree + 最小回归（必须先做）

如已有干净 worktree 可复用，否则新建：

```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v26-handout .worktrees/owner-b-20260226-writing-mode-v26-handout origin/main
cd .worktrees/owner-b-20260226-writing-mode-v26-handout

python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

交付（入库）：

- `notes/owner_b_v26_handout_preflight.md`（记录 HEAD、3 项测试 PASS）。

### B152. 产出单文件会议 Handout（可直接转发）

Create（入库）：

- `docs/reviews/2026-02-26/meeting-handout-v26.md`

内容组织建议（不重复造轮子，尽量链接既有材料）：

1. 结论 10 行（Plan‑B only / feature-loss v2 冻结 / Plan‑B+weak No‑Go / `N=0`）。
2. 三行关键数据（canonical full600 + seg200_260 full600），**只引用 v26 report-pack 真源**。
3. anti-cherrypick 摘要（seg300/400/600/1800 smoke200 delta + template hygiene 防守句）。
4. Scope + Limitations（短预算收敛性/时序稳定性；未测 Plan‑B + Feature Loss 作为 future work）。
5. 会议播放清单（指向 `outputs/qualitative/planb_vs_baseline/*.mp4`；若 A 提供 clips/frames notes，则再补链接）。
6. 证据入口（v26 report-pack 四件套 + v26 evidence tar SHA 的索引来源 `SHA256SUMS.txt`）。
7. 附：Q&A 入口（链接到 `docs/writing/planb_qa_cards_v26.md`）。

验收：

- Handout 内任何数字都能追溯到 `docs/report_pack/2026-02-26-v26/metrics.csv` 或 `scoreboard.md`。
- 无新增 report-pack 版本号（不生成 v27/vXX）。

### B153. Claim 审计（修辞一致性检查 + 必要时小修文稿）

检查目标：堵住两类高频攻击面。

1) Mutual NN 过度包装  
- 必须维持口径：Mutual NN = stabilizer（主要体现在 tLPIPS 稳定性），不宣称其为主要 PSNR 来源。

2) 绝对 PSNR 原罪  
- Scope 必须写死“短预算（600 steps）收敛性与时序稳定性”，避免“高保真上限”暗示。

Run（仅做检索与小修，不改数值）：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-handout
rg -n \"Mutual NN|核心贡献|主要来源|high-fidelity|高保真\" docs/writing notes/planb_verdict_writeup_owner_b.md
```

若发现不一致表述，最小修改以下文件（入库）：

- `docs/writing/planb_onepager_v26.md`
- `docs/writing/planb_qa_cards_v26.md`
- `notes/planb_verdict_writeup_owner_b.md`
- `docs/writing/planb_paper_outline.md`

验收：

- 文稿口径与 `docs/decisions/2026-02-26-planb-v26-freeze.md` 一致；
- 不引入任何新数字或新实验结论。

### B154. 接线 A 的会议资产清单（若到位）

当 `notes/planb_meeting_assets_v26_owner_a.md` 入库后：

- 在 `docs/reviews/2026-02-26/meeting-handout-v26.md` 增加一行链接（clips/frames/播放顺序）。
- 在 `docs/writing/planb_onepager_v26.md` 的播放清单处补充 “会议短片见 …”。

验收：引用为仓库相对路径，不使用 worktree 绝对路径。

### B155. 回归 + 合入主线

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-handout
for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1

git add docs/reviews/2026-02-26/meeting-handout-v26.md notes/owner_b_v26_handout_preflight.md
# 如 B153/B154 有额外修改，再补充 git add
git commit -m \"docs(review): add v26 meeting handout and claim-audit pass\"

git fetch origin
git rebase origin/main
git push origin HEAD:main
```

验收：

- `origin/main` 可见 handout + preflight；
- 提交不包含 `outputs/`、`data/`、`*.tar.gz`。

## 4) 并行性说明（与 Owner A）

- B151–B153 可立即执行，不依赖 A 的 clips 产物。
- A 若完成 `notes/planb_meeting_assets_v26_owner_a.md`，B154 只做接线与轻量文字补充即可。

