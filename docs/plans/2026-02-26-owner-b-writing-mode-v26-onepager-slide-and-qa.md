# Owner B 后续计划：Writing Mode（v26 冻结期）一页纸 + Slide 大纲 + Q&A 卡片（No‑GPU）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner B（No‑GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

在不使用 GPU、不新增任何训练、不改 `protocol_v1` 与数值逻辑的前提下，把 v26 证据链“翻译”为可直接用于：

- 组会/导师讨论的 **一页纸**（5 分钟扫完）
- 10–12 分钟的 **slide 讲稿大纲**（含播放视频顺序）
- **Q&A 防守卡片**（针对常见质疑给一致口径）

并把入口写进索引，减少“信息散落在 20 份 notes 里”的沟通成本。

## 1) 约束（必须遵守）

- 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`），不新增 smoke200/full600。
- 不改协议：不改 `docs/protocols/protocol_v1.yaml`；任何协议变更必须走 `protocol_v2`（本计划不做）。
- 不入库大文件：`data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 允许入库：`docs/`、`notes/`、`scripts/`、`scripts/tests/`、`artifacts/report_packs/SHA256SUMS.txt`（仅在确需登记新 tar 的情况下；本计划默认不新打 tar）。
- 会中数字引用口径：只允许引用 v26 report-pack 快照：
  - `docs/report_pack/2026-02-26-v26/metrics.csv`
  - `docs/report_pack/2026-02-26-v26/scoreboard.md`
  - `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
  - `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`

## 2) 输入依赖（不阻塞推进，但需预留接入口）

Owner A 在冻结期允许做 No‑GPU 资产整理与审计（不新增训练），计划产物（若已完成则纳入；若未完成则先留 TODO 位不影响交付）：

- `notes/planb_v26_audit_owner_a.md`
- `notes/planb_table1_v26_owner_a.md`
- `notes/planb_qualitative_frames_v26_owner_a.md`
- `notes/handoff_planb_v26_assets_owner_a.md`

## 3) 任务分解（B131–B136）

### B131. 建立隔离 worktree + 预检对齐（必须先做）

Run：
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v26-meeting .worktrees/owner-b-20260226-writing-mode-v26-meeting origin/main
cd .worktrees/owner-b-20260226-writing-mode-v26-meeting

# worktree 默认 outputs 为空壳：为报表工具对齐主阵地口径
ln -s /root/projects/4d-recon/outputs outputs

python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

交付（入库）：

- `notes/owner_b_v26_meeting_preflight.md`：记录 HEAD、依赖路径存在性、4 个测试 PASS。

### B132. 产出“一页纸”（会议前读物，强制收口到 v26 决议）

Create（入库）：

- `docs/writing/planb_onepager_v26.md`

内容必须包含（每项 1–3 行，避免长篇）：

1. 当前进度（已完成哪些 full600 / smoke200 / anti-cherrypick / template hygiene / qualitative / ablation）。
2. 当前路线选择（Plan‑B only；feature-loss v2 冻结；Plan‑B+weak No‑Go）。
3. 三行关键数据（canonical baseline_600 / planb_init_600 / feature_loss_v2_postfix_600；以及 seg200_260 的 planb vs baseline）。
4. anti-cherrypick 摘要（列出 seg300/400/600/1800 smoke200 的 delta，与“template hygiene 已做”的一句话防守）。
5. Scope 声明（短预算收敛性与时序稳定性；不声称高保真上限）。
6. Limitations（未测 Plan‑B+Feature Loss；原因=预算；写成 future work）。
7. 证据入口（v26 report-pack 四件套 + evidence tar SHA 行号来源 `SHA256SUMS.txt`）。
8. 会议播放清单（canonical/seg200_260 必选 + 任选 1 个 seg smoke200；指向 `outputs/qualitative/planb_vs_baseline/*.mp4`）。

### B133. 产出 slide 讲稿大纲（10–12 分钟，先视频后数字）

Create（入库）：

- `docs/writing/planb_talk_outline_v26.md`

结构强制按以下顺序（防“防守过载”）：

1. 先播 side-by-side（5 分钟内播完）：canonical → seg200_260 →（可选）seg300/400/600/1800 其一。
2. 再给主表（Table 1）：canonical + seg200_260 的 full600（PSNR/SSIM/LPIPS/tLPIPS + Δ）。
3. 再给 anti-cherrypick：多切片 smoke200 同向增益（附“template hygiene 重跑”一句话）。
4. 最后才是防守附录（各 1 张/1 页）：Gate‑S1 统计、component ablation、feature-loss v2 负结果与归因、为何不做组合实验（Limitation）。
5. Ending：决议复述（Plan‑B only、`N=0`、写作冲刺交付物）。

### B134. 产出 Q&A 防守卡片（统一话术，提前拆雷）

Create（入库）：

- `docs/writing/planb_qa_cards_v26.md`

必须覆盖并给出“可直接念”的回答（每题 3–6 句）：

- cherry-pick 质疑（为什么不是挑帧/挑段/挑 seed）
- 绝对 PSNR 偏低（scope + 视觉证据打法）
- “Plan‑B 是不是速度投机”（承认“打破收敛陷阱”为主因，但用 Gate‑S1 与消融解释其非异常投机）
- Mutual NN 的真实定位（必要 stabilizer，主要体现在 tLPIPS 稳定性；避免宣称其为主要 PSNR 来源）
- 为什么冻结 feature-loss v2、为什么不测 Plan‑B + Feature Loss（正交 + 预算限制 + limitation/future work）
- 为什么 weak cue No‑Go（smoke200 证据不足且 tLPIPS 未同向）

### B135. 更新写作入口与索引（减少“找不到最新入口”）

Modify（入库）：

- `docs/writing/planb_paper_outline.md`：增加 links 到 onepager/talk_outline/qa_cards；写死 scope 与 limitation 口径。
- `notes/planb_verdict_writeup_owner_b.md`：把“Mutual NN 主要贡献”类表述修为 stabilizer 口径；引用路径统一指向 v26 report-pack。
- `docs/README.md`：在索引中补充 v26 freeze 决议与三份写作材料入口（可选，但推荐）。

验收：

- 任意一处引用指标数字必须可追溯到 `docs/report_pack/2026-02-26-v26/metrics.csv` 或 `scoreboard.md`。
- 不引入新的 report-pack 版本号（避免口径漂移）；只做写作入口链接更新。

### B136. 回归 + 合入（必须）

Run：
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v26-meeting
for t in scripts/tests/test_*.py; do python3 "$t"; done
git status --porcelain=v1
```

提交规范：

- 只提交 `docs/writing/*`、`notes/*`、`docs/README.md`（若修改）；不提交任何 `outputs/`、`data/`、`*.tar.gz`。
- Commit message 建议：
  - `docs(writing): add v26 onepager/talk outline/qa cards`
  - `docs(planb): align verdict wording with v26 freeze decision`

## 4) 并行性说明（与 Owner A）

- B131–B134 可立即执行，不依赖 A 的新产物。
- A 若补充 `notes/planb_*_v26_owner_a.md`，B 在 B135 阶段把路径与推荐主图/视频清单补进 onepager 与 talk outline 即可；不需要重跑任何指标。

