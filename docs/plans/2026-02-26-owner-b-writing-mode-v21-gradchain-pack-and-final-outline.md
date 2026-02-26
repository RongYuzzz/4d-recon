# Writing Mode v21 (Owner B, No-GPU) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不使用 GPU、不新增训练预算的前提下，把 Plan‑B 主线与 feature‑loss 负结果的“可辩护证据链”收口成 v21 report-pack/evidence，并给出可直接用于论文/答辩的写作骨架与防守口径。

**Architecture:** 以 `docs/decisions/2026-02-26-planb-pivot.md` 为唯一决议真源；B 只做 CPU/IO 的分析脚本、文档收口与打包刷新。依赖 A 的 GPU 产物仅限“证据落盘”（梯度链 CSV 与 postfix_600 主阵地暴露），B 的代码与写作改动可先行并行推进。

**Tech Stack:** Python（`scripts/*.py`）、bash、`scripts/tests/test_*.py`、`scripts/{build_report_pack.py,summarize_scoreboard.py,pack_evidence.py}`、`docs/report_pack/*` 快照机制。

---

## 约束（必须遵守）

- 全程 No‑GPU：不运行任何训练脚本（`run_train_*.sh`），不新增 full600 / smoke200。
- 不改 `docs/protocols/protocol_v1.yaml` 与 canonical 数据定义；任何“协议变更”必须新建 `protocol_v2`（本计划不做）。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库；只提交 `docs/`、`notes/`、`scripts/`、`scripts/tests/`、`artifacts/report_packs/SHA256SUMS.txt`。
- `git worktree` 默认不会带上主阵地的大体积 `outputs/`：刷新 report-pack 时必须在 worktree 内创建 `outputs -> /root/projects/4d-recon/outputs` 的 symlink，保证路径口径与可复现性一致。

---

### Task 1: 建立隔离工作区 + 预检对齐

**Files:**
- Create: (none)
- Modify: (none)
- Test: `scripts/tests/test_pack_evidence.py`, `scripts/tests/test_build_report_pack.py`, `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 创建 worktree（隔离写作/脚本改动）**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v21 .worktrees/owner-b-20260226-writing-mode-v21 origin/main
cd .worktrees/owner-b-20260226-writing-mode-v21
git status -sb
```

Expected: worktree 创建成功，且 `git status` 干净。

**Step 2: 最小回归（确保主线没崩）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected: 全 PASS。

**Step 3: Commit（可选）**

说明：本 Task 无代码变更，不提交。

---

### Task 2: Scoreboard 自动生成“结论要点”（移除 TODO，占位变可引用）

**Files:**
- Modify: `scripts/summarize_scoreboard.py`
- Modify: `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 先写失败测试（要求不再出现 TODO）**

Edit `scripts/tests/test_summarize_scoreboard.py`：
- 把断言从 `结论要点（占位）` 改为期望 `结论要点（自动生成）`
- 增加断言：`"TODO"` 不得出现在产物 markdown 中
- 增加断言：至少包含三条自动要点关键字（例如 `PSNR 最优`、`tLPIPS 最优`、`风险提示`）

**Step 2: 运行测试，确认红灯**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected: FAIL（因为当前 `summarize_scoreboard.py` 仍输出 TODO）。

**Step 3: 最小实现（自动结论要点）**

Edit `scripts/summarize_scoreboard.py`：
- 将：
  - `## 结论要点（占位）` + 3 条 TODO
- 替换为（示例，按实际实现输出）：
  - `## 结论要点（自动生成）`
  - `- PSNR 最优：<run> (<value>)`
  - `- tLPIPS 最优：<run> (<value>)`
  - `- 风险提示：<一句话复用现有风险判断口径>`

实现建议（避免引入新依赖）：
- 在 `selected` 内遍历，分别找 psnr 最大与 tlpips 最小（忽略 `None`）
- 风险提示复用已生成的 `risk_lines` / “无风险/无法判断”结论（组装为一句话）

**Step 4: 运行测试，确认绿灯**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected: PASS。

**Step 5: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py
git commit -m "feat(scoreboard): auto-generate takeaways and remove TODO placeholders"
```

---

### Task 3: 生成“Plan-B anti-cherrypick 摘要表”（脚本化，避免手抄出错）

**Files:**
- Create: `scripts/summarize_planb_anticherrypick.py`
- Create: `scripts/tests/test_summarize_planb_anticherrypick.py`

**Step 1: 写失败测试（dummy metrics.csv -> 期望 markdown 含 3 段）**

Create `scripts/tests/test_summarize_planb_anticherrypick.py`（建议用 `tempfile.TemporaryDirectory(dir=REPO_ROOT)`）：
- 构造最小 `metrics.csv`（字段对齐 `scripts/build_report_pack.py` 的输出）
- 至少包含三组数据：
  - canonical：`.../selfcap_bar_8cam60f/baseline_600` 与 `.../selfcap_bar_8cam60f/planb_init_600`（step599, stage=test）
  - seg200_260：`.../selfcap_bar_8cam60f_seg200_260/baseline_600` 与 `.../planb_init_600`（step599, stage=test）
  - seg400_460：`.../selfcap_bar_8cam60f_seg400_460/baseline_smoke200` 与 `.../planb_init_smoke200`（step199, stage=test）
- 运行脚本后断言输出 markdown 存在：
  - `## Canonical`
  - `## seg200_260`
  - `## seg400_460`
  - 且每段包含 `ΔPSNR`、`ΔLPIPS`、`ΔtLPIPS`

**Step 2: 运行测试，确认红灯（脚本不存在）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: FAIL（找不到脚本或返回码非 0）。

**Step 3: 最小实现脚本（只读 metrics.csv，输出 markdown）**

Create `scripts/summarize_planb_anticherrypick.py`：
- 输入参数：
  - `--metrics_csv`（默认 `outputs/report_pack/metrics.csv`）
  - `--out_md`（默认 `outputs/report_pack/planb_anticherrypick.md`）
- 选择逻辑（写死，避免争论）：
  - canonical：`select_contains=selfcap_bar_8cam60f/` 且不含 `_seg`
  - seg200_260：`select_contains=selfcap_bar_8cam60f_seg200_260`
  - seg400_460：`select_contains=selfcap_bar_8cam60f_seg400_460`
- 每段固定挑选：
  - baseline：优先 `baseline_600@test@599`；若缺失则回退 `baseline_smoke200@test@199`
  - planb：优先 `planb_init_600@test@599`；若缺失则回退 `planb_init_smoke200@test@199`
- 输出 markdown：
  - 一张两行对比表（baseline vs planb）
  - 一行 Delta（planb - baseline）

**Step 4: 运行测试，确认绿灯**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: PASS。

**Step 5: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
git add scripts/summarize_planb_anticherrypick.py scripts/tests/test_summarize_planb_anticherrypick.py
git commit -m "feat(report-pack): add planb anti-cherrypick summary helper"
```

---

### Task 4: 等待 A 交付后，补齐 feature-loss “梯度链”归因项（文档收口）

**Files:**
- Modify: `notes/feature_loss_failure_attribution_minpack.md`
- Modify: `docs/report_pack/2026-02-26-v20/failure_cases.md`（或在 v21 刷新时写入 `outputs/report_pack/failure_cases.md`）

**Step 1: 拉取最新 main，确认 A 的交付已合入**

依赖 A 的入库交付（来自 `docs/plans/2026-02-26-owner-a-featureloss-gradchain-and-postfix-expose.md`）：
- `notes/feature_loss_v2_grad_chain_owner_a.md`
- `notes/handoff_feature_loss_v2_grad_chain_owner_a.md`

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
git fetch origin
git rebase origin/main
ls -la notes/feature_loss_v2_grad_chain_owner_a.md notes/handoff_feature_loss_v2_grad_chain_owner_a.md
```

Expected: 两个文件存在。

**Step 2: 更新最小归因包文档（把“梯度链”改成 DONE，并给出证据路径）**

Edit `notes/feature_loss_failure_attribution_minpack.md`：
- 增加/更新一条：“(5) 梯度链检查：`outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv` + `notes/feature_loss_v2_grad_chain_owner_a.md`”
- 明确口径：目的为排除“实现无效/梯度链断”，不等价于“feature-loss 可行”。

**Step 3: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
git add notes/feature_loss_failure_attribution_minpack.md
git commit -m "docs(feature-loss): close minpack with grad-chain evidence pointer"
```

---

### Task 5: 刷新 report-pack/evidence 到 v21（含新脚本产物 + A 的梯度链证据）

**Files:**
- Create: `docs/report_pack/2026-02-26-v21/*`
- Modify: `artifacts/report_packs/SHA256SUMS.txt`

**Step 1: 刷新 outputs/report_pack（指向主阵地 outputs）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21

# 通过 symlink 复用主阵地 outputs，避免 worktree outputs 为空导致“报表缺行”
ln -sfn /root/projects/4d-recon/outputs outputs

python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/planb_anticherrypick.md
```

Expected:
- `outputs/report_pack/metrics.csv` 更新且包含 `planb_init_600`、`seg200_260 planb_init_600`、`seg400_460 planb_init_smoke200` 行
- `outputs/report_pack/scoreboard.md` 不再含 TODO
- `outputs/report_pack/planb_anticherrypick.md` 生成

**Step 2: 生成 v21 evidence tar + 登记 SHA**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/pack_evidence.py --repo_root "$(pwd)" --out_tar /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v21.tar.gz
sha256sum /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v21.tar.gz >> artifacts/report_packs/SHA256SUMS.txt
```

Expected: tar 生成成功，`SHA256SUMS.txt` 追加一行。

**Step 3: 生成 docs 快照 v21（manifest 必须来自 tar 解包）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
mkdir -p docs/report_pack/2026-02-26-v21

cp -a outputs/report_pack/metrics.csv \
  outputs/report_pack/scoreboard.md \
  outputs/report_pack/ablation_notes.md \
  outputs/report_pack/failure_cases.md \
  docs/report_pack/2026-02-26-v21/

# 新增：anti-cherrypick 脚本输出（写作防守用）
cp -a outputs/report_pack/planb_anticherrypick.md \
  docs/report_pack/2026-02-26-v21/

tar -xzf /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v21.tar.gz -O manifest_sha256.csv \
  > docs/report_pack/2026-02-26-v21/manifest_sha256.csv
```

Expected: `docs/report_pack/2026-02-26-v21/` 至少包含 6 个文件（含 `planb_anticherrypick.md`）。

**Step 4: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
git add docs/report_pack/2026-02-26-v21 artifacts/report_packs/SHA256SUMS.txt
git commit -m "docs(report-pack): snapshot v21 (planb anticherrypick + grad-chain ready)"
```

---

### Task 6: 写作骨架（可直接贴到论文/答辩）与路径索引

**Files:**
- Create: `docs/writing/planb_paper_outline.md`
- Modify: `docs/README.md`

**Step 1: 新建写作骨架文档（不追求完美，先可引用）**

Create `docs/writing/planb_paper_outline.md`，建议包含以下固定小节（每节 3-7 行即可）：
- 摘要（1 段，强调：可复现协议 + 负结果机制归因 + Plan‑B 物理初始化修正）
- 方法（Plan‑B 定义 + mutual NN 组件必要性证据）
- 实验（canonical 主表 + seg200_260/seg400_460 作为 anti‑cherrypick 附录）
- 负结果与失败归因（feature-loss v2：对齐/敏感性/gating/梯度链证据路径）
- 复现（指向 `docs/protocol.yaml`、`docs/execution/2026-02-26-planb.md`、最新 `docs/report_pack/*`）

硬要求：每个结论后都给出证据路径（文件路径即可，不要写 URL）。

**Step 2: docs index 增补 writing 入口**

Edit `docs/README.md`：
- 在索引中新增一条：
  - `docs/writing/planb_paper_outline.md`（写作骨架与证据路径索引）

**Step 3: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
mkdir -p docs/writing
git add docs/writing/planb_paper_outline.md docs/README.md
git commit -m "docs(writing): add planb paper outline with evidence pointers"
```

---

### Task 7: 合入 main（rebase 后 push）

**Files:**
- (all committed changes)

**Step 1: 最终回归（只跑关键测试，避免漏）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: 全 PASS。

**Step 2: rebase + push**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v21
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected: push 成功。
