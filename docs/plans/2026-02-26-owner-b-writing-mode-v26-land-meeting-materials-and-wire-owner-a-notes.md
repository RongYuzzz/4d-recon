# Owner B 后续计划：Writing Mode（v26 冻结期）会议材料合入 + 去 TODO（No‑GPU）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner B（No‑GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

在不使用 GPU、不新增训练、不改 `protocol_v1` 与数值逻辑的前提下：

1. 将 v26 会议写作三件套（onepager / talk outline / Q&A cards）**合入 `origin/main`**，让团队有统一入口。
2. 在 Owner A 的 v26 资产 notes 入库后，去掉 onepager 中的 TODO 占位，改为**可点击的真实路径引用**。
3. 维持“唯一数字口径”：所有数值只引用 `docs/report_pack/2026-02-26-v26/` 四件套。

## 1) 约束（必须遵守）

- 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`），不新增 smoke200/full600。
- 不改协议：不改 `docs/protocols/protocol_v1.yaml`；不改训练数值逻辑。
- 不入库大文件：`data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 只允许提交：`docs/`、`notes/`（本计划不应修改 `scripts/`；如确需改动必须先解释原因并补测试）。

## 2) 前置状态（当前已完成但未合入）

Owner B 已有分支/提交（示例）：

- `c9f4ec2`：新增 `docs/writing/planb_{onepager,talk_outline,qa_cards}_v26.md` 并更新写作入口
- `8663ef8`：对齐 `notes/planb_verdict_writeup_owner_b.md` 口径（Mutual NN = stabilizer）并补 preflight

若实际提交号不同，以本地 `git log --oneline origin/main..HEAD` 为准。

## 3) 任务分解（B141–B144）

### B141. 合入会议材料到 `origin/main`（不阻塞 A）

在 worktree（如：`/root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting`）执行：

```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting
git fetch origin
git rebase origin/main

for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1

git push origin HEAD:main
```

验收：

- push 成功，且入库文件仅在 `docs/` 与 `notes/`。
- `docs/writing/planb_onepager_v26.md` 明确写死：新增 full600 `N=0`、feature-loss v2 冻结、Plan‑B+weak No‑Go。
- 所有数值引用只指向 `docs/report_pack/2026-02-26-v26/*`。

### B142. 等待 A 的 notes 入库后，去掉 TODO 占位（wire-up）

当 `origin/main` 出现以下 4 个文件后再执行（A 会给你 commit hash）：

- `notes/planb_v26_audit_owner_a.md`
- `notes/planb_qualitative_frames_v26_owner_a.md`
- `notes/planb_table1_v26_owner_a.md`
- `notes/handoff_planb_v26_assets_owner_a.md`

修改（入库）：

- `docs/writing/planb_onepager_v26.md`
  - 将 “Owner A 接入口 TODO” 替换为上述 4 个真实路径（可点击）。
- （可选但推荐）`docs/writing/planb_talk_outline_v26.md`
  - 在“播放清单/抽帧主图组”处补一句：主图索引见 `notes/planb_qualitative_frames_v26_owner_a.md`。
- （可选）`docs/writing/planb_paper_outline.md`
  - 将 Table‑1 的来源补为 `notes/planb_table1_v26_owner_a.md`（同时保留 v26 report-pack 真源路径）。

执行：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting
git fetch origin
git rebase origin/main

$EDITOR docs/writing/planb_onepager_v26.md
# optional:
# $EDITOR docs/writing/planb_talk_outline_v26.md
# $EDITOR docs/writing/planb_paper_outline.md

for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1

git add docs/writing/planb_onepager_v26.md
# optional:
# git add docs/writing/planb_talk_outline_v26.md docs/writing/planb_paper_outline.md
git commit -m "docs(writing): wire up owner-a v26 audit/table/frames notes"
git push origin HEAD:main
```

验收：

- onepager 中不再出现 TODO 占位。
- 引用路径均为仓库内相对路径（`notes/...` / `docs/...`），无 worktree 绝对路径。

### B143. 最终自检（会前 5 分钟版）

```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py

rg -n "新增 full600 `N=0`" docs/writing/planb_onepager_v26.md
rg -n "Mutual NN 是 stabilizer" notes/planb_verdict_writeup_owner_b.md
```

验收：测试 PASS；关键口径句存在。

### B144. 会后可选清理（不改变数值口径）

仅当发现写作入口存在历史残留标题/链接时做：

- 统一将“口径真源”链接指向 v26 report-pack（不生成新 vXX）。
- 不新增任何新的 report-pack tarball；避免版本号滚动造成口径漂移。

## 4) 并行性说明（与 Owner A）

- B141 可立即执行（把会议材料先合入主线，不阻塞 A）。
- A 入库 4 个 notes 后，B142 再做一次小 patch 去 TODO，占用时间很短。

