# Owner A 后续计划：Writing Mode（v26 冻结期）资产入库 + unblock 写作材料（不新增训练）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0 可用但本计划默认不使用 GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

把 Owner A 已完成的 v26 资产整理与审计产物**入库到 `origin/main`**，以便：

- Owner B 的 `planb_onepager_v26.md` / `talk_outline` / `qa_cards` 去掉 TODO 占位并引用真实路径；
- 会议/写作引用链闭环（审计记录 + Table‑1 + 定性主图索引 + handoff）。

## 1) 约束（必须遵守）

- 禁止新增训练：不运行任何 `run_train_*.sh`，不新增任何 smoke200/full600。
- 不改 `docs/protocols/protocol_v1.yaml` 与训练数值逻辑。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 只允许提交：`notes/*`（本计划默认不修改脚本/测试）。

## 2) 任务分解（A141–A144）

### A141. 确认工作区与依赖（No‑GPU，5 分钟）

定位到 A 的 worktree（如：`/root/projects/4d-recon/.worktrees/owner-a-v26-assets-audit`），执行：

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-v26-assets-audit
git status -sb
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

验收：4 项 PASS；`git status` 仅包含计划内 `notes/*` 新增。

### A142. 入库提交（只提交 4 个 notes 文件）

期望入库文件（必须都在 `notes/` 下）：

- `notes/planb_v26_audit_owner_a.md`
- `notes/planb_qualitative_frames_v26_owner_a.md`
- `notes/planb_table1_v26_owner_a.md`
- `notes/handoff_planb_v26_assets_owner_a.md`

执行：
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-v26-assets-audit
git add \
  notes/planb_v26_audit_owner_a.md \
  notes/planb_qualitative_frames_v26_owner_a.md \
  notes/planb_table1_v26_owner_a.md \
  notes/handoff_planb_v26_assets_owner_a.md

git commit -m "docs(planb): add v26 audit + table1 + qualitative frame index (owner-a)"
```

验收：

- commit 只包含以上 4 个文件；
- 不包含任何 `outputs/`、`data/`、`*.tar.gz`。

### A143. Rebase + 推送到 `origin/main`

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-v26-assets-audit
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

验收：push 成功；记录最终 commit hash（供 B 引用）。

### A144. Handoff 给 Owner B（unblock TODO 占位）

把以下信息发给 Owner B（写进 handoff 或消息均可）：

- 上述入库 commit hash；
- 4 个 notes 路径（上面列表）；
- `planb_onepager_v26.md` 里 “Owner A 接入口 TODO” 可直接替换为真实路径。

验收：B 可在合入阶段把 onepager/talk/qa 的 TODO 占位去掉（B 自己执行）。

## 3) 收尾检查（主仓）

在主仓验证已入库：
```bash
cd /root/projects/4d-recon
git pull --ff-only
ls -la notes/planb_v26_audit_owner_a.md \
      notes/planb_qualitative_frames_v26_owner_a.md \
      notes/planb_table1_v26_owner_a.md \
      notes/handoff_planb_v26_assets_owner_a.md
```

验收：4 文件存在且可读。

