# Writing Mode v22 (Owner B, No-GPU) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 A（GPU0）完成 `Plan-B + weak` smoke200 试验后，B 以 No‑GPU 方式将该结论并入写作与证据链：补齐 anti‑cherrypick 的定性 side-by-side、刷新 report-pack/evidence 到 v22，并更新写作骨架/口径到可直接交付状态。

**Architecture:** B 不改协议、不新增训练，只做：定性资产生成（ffmpeg）、报表链路刷新（build/summarize/analyze）、写作与快照打包（docs/report_pack + evidence tar + SHA）。依赖 A 的产物仅限于两条新 smoke200 run + notes handoff；其余均可并行推进。

**Tech Stack:** bash + ffmpeg（`scripts/make_side_by_side_video.sh`）、Python 分析脚本（`scripts/{build_report_pack.py,summarize_scoreboard.py,summarize_planb_anticherrypick.py,analyze_smoke200_m1.py,pack_evidence.py}`）、文档（`docs/report_pack/*`, `docs/writing/*`, `notes/*`）。

---

## 约束（必须遵守）

- 全程 No‑GPU：不运行任何 `run_train_*.sh`，不新增任何 smoke/full 训练。
- 不改 `docs/protocols/protocol_v1.yaml`，不改数据口径。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库；只提交 `docs/`、`notes/`、`scripts/`、`scripts/tests/`、`artifacts/report_packs/SHA256SUMS.txt`。

---

### Task 1: 建立隔离 worktree + 预检对齐

**Files:**
- Create: (none)
- Modify: (none)
- Test: `scripts/tests/test_pack_evidence.py`, `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add -b owner-b-20260226-writing-mode-v22 .worktrees/owner-b-20260226-writing-mode-v22 origin/main
cd .worktrees/owner-b-20260226-writing-mode-v22
git status -sb
```

Expected: 工作区干净。

**Step 2: 最小回归**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_summarize_scoreboard.py
```

Expected: PASS。

---

### Task 2: 定性证据增强（seg200_260 / seg400_460 side-by-side）

**Files:**
- Modify: `docs/execution/2026-02-26-planb-qualitative.md`

**Step 1: 生成 seg200_260 side-by-side（full600）**

说明：把输出写到 `outputs/qualitative/planb_vs_baseline/`，以便 `scripts/pack_evidence.py` 自动收录 `*.mp4`。

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
ln -sfn /root/projects/4d-recon/outputs outputs

bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/baseline_600/videos/traj_4d_step599.mp4 \
  --right outputs/protocol_v1_seg200_260/selfcap_bar_8cam60f_seg200_260/planb_init_600/videos/traj_4d_step599.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg200_260_step599.mp4 \
  --left_label baseline_seg200_260_600 \
  --right_label planb_seg200_260_600 \
  --overwrite
```

Expected: `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4` 存在。

**Step 2: 生成 seg400_460 side-by-side（smoke200）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
bash scripts/make_side_by_side_video.sh \
  --left  outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/baseline_smoke200/videos/traj_4d_step199.mp4 \
  --right outputs/protocol_v1_seg400_460/selfcap_bar_8cam60f_seg400_460/planb_init_smoke200/videos/traj_4d_step199.mp4 \
  --out_dir outputs/qualitative/planb_vs_baseline \
  --out_name planb_vs_baseline_seg400_460_step199.mp4 \
  --left_label baseline_seg400_460_smoke200 \
  --right_label planb_seg400_460_smoke200 \
  --overwrite
```

Expected: `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4` 存在。

**Step 3: 更新执行文档（把两条命令写进 runbook）**

Edit `docs/execution/2026-02-26-planb-qualitative.md`：
- 增加 “seg200_260 / seg400_460” 两段，包含上述命令与输出文件名。
- 明确：这些 mp4 不入库，但会被 evidence tar 自动收录（路径不变时）。

**Step 4: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
git add docs/execution/2026-02-26-planb-qualitative.md
git commit -m "docs(qualitative): add seg200_260 and seg400_460 side-by-side commands"
```

---

### Task 3: 等待 A 产物落地（Plan-B + weak smoke200），并做路径核验

**Files:**
- Modify: (none)
- Create: (none)

**Step 1: 拉取最新 main**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
git fetch origin
git rebase origin/main
```

Expected: rebase 成功。

**Step 2: 核验 A 交付（路径必须存在）**

依赖 A 的新 run（不入库但主阵地可见）：
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200/stats/test_step0199.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200/stats/test_step0199.json`

依赖 A 的入库 notes：
- `notes/planb_plus_weak_smoke200_owner_a.md`
- `notes/handoff_planb_plus_weak_smoke200_owner_a.md`

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
ln -sfn /root/projects/4d-recon/outputs outputs

ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200/stats/test_step0199.json
ls -la outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200/stats/test_step0199.json
ls -la notes/planb_plus_weak_smoke200_owner_a.md notes/handoff_planb_plus_weak_smoke200_owner_a.md
```

Expected: 全部存在。

---

### Task 4: 刷新报表并生成 “Plan-B + weak” smoke200 对比表（不新增训练）

**Files:**
- Modify: `outputs/report_pack/ablation_notes.md`（不入库，但会进入 evidence tar）
- Modify: `outputs/report_pack/failure_cases.md`（不入库，但会进入 evidence tar）

**Step 1: 刷新 metrics.csv + canonical scoreboard**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
python3 scripts/build_report_pack.py --outputs_root outputs --out_dir outputs/report_pack
python3 scripts/summarize_scoreboard.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/scoreboard.md
python3 scripts/summarize_planb_anticherrypick.py --metrics_csv outputs/report_pack/metrics.csv --out_md outputs/report_pack/planb_anticherrypick.md
```

Expected:
- `outputs/report_pack/metrics.csv` 含两条新 smoke200 行（run_dir basename 为 `planb_control_weak_nocue_smoke200` 与 `planb_ours_weak_smoke200_w0.3_end200`）
- `outputs/report_pack/scoreboard.md` 无 TODO，且包含 `feature_loss_v2_postfix_600`

**Step 2: 生成 Plan-B+weak smoke200 对比表（baseline 选 planb_init_smoke200）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
python3 scripts/analyze_smoke200_m1.py \
  --metrics_csv outputs/report_pack/metrics.csv \
  --out_md outputs/report_pack/planb_plus_weak_smoke200.md \
  --select_prefix outputs/protocol_v1/ \
  --select_contains selfcap_bar_8cam60f \
  --baseline_regex '^planb_init_smoke200$' \
  --step 199 \
  --stage test
```

Expected: `outputs/report_pack/planb_plus_weak_smoke200.md` 生成，包含 ΔPSNR/ΔLPIPS/ΔtLPIPS。

**Step 3: 更新 outputs/report_pack 文稿（加入“Plan-B + weak”结论入口）**

Edit `outputs/report_pack/ablation_notes.md`：追加一小节 “Plan-B + weak（smoke200）”，只写两点：
- 三行对比（planb_init_smoke200 / planb_control_weak_nocue_smoke200 / planb_ours_weak_smoke200_w0.3_end200）
- 一句话结论（引用 A 的 `notes/planb_plus_weak_smoke200_owner_a.md`，避免手抄数值）

Edit `outputs/report_pack/failure_cases.md`：如 cue 在 Plan‑B 下仍负增益，追加一句 “cue 注入的负增益风险在 Plan‑B 下仍存在（smoke200）”；如转正则改为 “cue 在 Plan‑B 下转为可用（smoke200），但未获 full600 预算验证”。

---

### Task 5: 刷新 v22 docs 快照 + v22 evidence tar + SHA 登记（入库）

**Files:**
- Create: `docs/report_pack/2026-02-26-v22/*`
- Modify: `artifacts/report_packs/SHA256SUMS.txt`
- Modify: `notes/planb_verdict_writeup_owner_b.md`
- Modify: `docs/writing/planb_paper_outline.md`

**Step 1: 更新写作口径（把 Plan-B+weak 的结论写进去）**

Edit `notes/planb_verdict_writeup_owner_b.md`：
- 增加一段 “Plan-B + weak（smoke200）” 的结论与解释（引用 `outputs/report_pack/planb_plus_weak_smoke200.md` 与 A notes 路径）。

Edit `docs/writing/planb_paper_outline.md`：
- 在 “实验” 或 “失败归因” 中补充一句：cue 风险在 Plan‑B init 下是否仍成立（以 smoke200 证据为准），并给出路径指针。

**Step 2: 打包 v22 evidence tar + 登记 SHA**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
python3 scripts/pack_evidence.py --repo_root "$(pwd)" --out_tar /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v22.tar.gz
sha256sum /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v22.tar.gz >> artifacts/report_packs/SHA256SUMS.txt
```

Expected: tar 生成成功，`SHA256SUMS.txt` 追加 v22 行。

**Step 3: 生成 docs 快照 v22（manifest 必须来自 tar 解包）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
mkdir -p docs/report_pack/2026-02-26-v22

cp -a outputs/report_pack/metrics.csv \
  outputs/report_pack/scoreboard.md \
  outputs/report_pack/ablation_notes.md \
  outputs/report_pack/failure_cases.md \
  outputs/report_pack/planb_anticherrypick.md \
  outputs/report_pack/planb_plus_weak_smoke200.md \
  docs/report_pack/2026-02-26-v22/

tar -xzf /root/projects/4d-recon/artifacts/report_packs/report_pack_2026-02-26-v22.tar.gz -O manifest_sha256.csv \
  > docs/report_pack/2026-02-26-v22/manifest_sha256.csv
```

Expected: `docs/report_pack/2026-02-26-v22/` 至少包含 7 个文件。

**Step 4: Commit**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
git add docs/report_pack/2026-02-26-v22 artifacts/report_packs/SHA256SUMS.txt \
  notes/planb_verdict_writeup_owner_b.md docs/writing/planb_paper_outline.md \
  docs/execution/2026-02-26-planb-qualitative.md
git commit -m "docs(report-pack): snapshot v22 incl planb+weak smoke200 and more qualitative evidence"
```

---

### Task 6: 最终回归 + 合入 main

**Files:**
- (all committed changes)

**Step 1: 回归测试**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
python3 scripts/tests/test_pack_evidence.py
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py
```

Expected: 全 PASS。

**Step 2: rebase + push**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260226-writing-mode-v22
git fetch origin
git rebase origin/main
git push origin HEAD:main
```

Expected: push 成功。

