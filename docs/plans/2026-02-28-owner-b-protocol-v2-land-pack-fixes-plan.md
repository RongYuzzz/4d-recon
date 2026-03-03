# protocol_v2 Land Evidence-Pack Fixes + Refresh Offline Bundle Implementation Plan (Owner B / GPU1)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 “pack_evidence 在 worktree 下漏打 outputs symlink 子树” 的修复与 stage‑2 两份诊断（temporal diff / tLPIPS curve）**正式落到集成分支**，并在仓库根目录重打 `outputs/report_pack_2026-02-28.tar.gz` + 回填 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`，确保 doc 引用路径在离线包内可审计。

**Architecture:** 以已完成的执行分支 `owner-b/protocol-v2-tlpips-diagnostics-exec` 为 source-of-truth，把关键提交 merge/cherry-pick 到目标集成分支（默认 `owner-b/c2-full600-integration-livews`）；在目标分支下跑 `pytest`，然后在**仓库根目录**运行 `scripts/pack_evidence.py` 生成离线包，并用 tar 内的 `manifest_sha256.csv` 覆盖回填到 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`；最后做 tar 抽查（qualitative/mp4、vggt_cache、cue_mining、protocol_v1/v2 stats、stage‑2 diagnostics、notes）。

**Tech Stack:** `git`、`python3`、`pytest`、`tar`、`rg`。

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；本计划只做“落地/打包/文档闭环”。
- 产物路径保持不变：离线包仍为 `outputs/report_pack_2026-02-28.tar.gz`，manifest 快照仍为 `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`。
- `outputs/` 是本地大目录（gitignore），离线包与 manifest 需要可重复生成，但不要求在 git 中提交 tar。

---

### Task 0: Preflight（5-10 分钟）

**Files:**
- Read: `scripts/pack_evidence.py`
- Read: `docs/report_pack/2026-02-27-v2/README.md`
- Read: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

**Step 1: 确认 source 分支存在且包含关键提交**

Run:
```bash
git show --oneline -s e6b7230
git show --oneline -s dbf8064
git show --oneline -s c507a50
git show --oneline -s 8e28102
git show --oneline -s f195d1c
git show --oneline -s 851974c
git show --oneline -s cd71fdb
```
Expected: 7 条提交都可展示（覆盖：tLPIPS 曲线脚本+测试、tLPIPS note、stage‑2 指针与 manifest、pack_evidence symlink 修复、scoreboard/notes/manifest 跟踪、temporal diff top‑k 帧快照脚本+测试、temporal diff top‑k 帧快照 note）。

---

### Task 1: 创建干净 worktree 用于落地（5 分钟）

**Step 1: 新建 worktree（避免主目录脏状态导致冲突）**

Run:
```bash
git worktree add .worktrees/owner-b-land-v2-pack \
  -b owner-b/protocol-v2-land-v2-pack \
  owner-b/c2-full600-integration-livews
cd .worktrees/owner-b-land-v2-pack
```

**Step 2: 确认工作区干净**

Run:
```bash
git status --porcelain
```
Expected: 空输出（clean）。

---

### Task 2: 把修复与诊断落到目标分支（10-20 分钟）

**Step 1: 合并 source 分支（推荐 merge，保留线性历史也可 cherry-pick）**

Option A（推荐）:
```bash
git merge --no-ff owner-b/protocol-v2-tlpips-diagnostics-exec
git merge --no-ff owner-a/protocol-v2-temporal-diff-topk-frames
```

Option B（更可控，逐条 cherry-pick）:
```bash
git cherry-pick e6b7230 dbf8064 c507a50 8e28102 f195d1c 851974c cd71fdb
```

**Step 2: 解决冲突（如有）并确保关键文件存在**

必查文件：
- `scripts/pack_evidence.py`（应包含：top-level outputs symlink 搜索 + vggt_cache/cue_mining/gate_framediff + 避免 docs 侧 manifest 自引用）
- `scripts/tests/test_pack_evidence_follows_outputs_symlinks.py`
- `scripts/analyze_tlpips_curve_from_renders.py`
- `scripts/analyze_temporal_diff_from_renders.py`
- `scripts/viz_temporal_diff_topk_frames.py`
- `scripts/tests/test_viz_temporal_diff_topk_frames_contract.py`
- `notes/protocol_v2_tlpips_curve_diagnostics.md`
- `notes/protocol_v2_stage2_tradeoff_qual.md`
- `notes/protocol_v2_temporal_diff_topk_frames.md`
- `docs/report_pack/2026-02-27-v2/README.md`
- `docs/report_pack/2026-02-27-v2/scoreboard*.md`

---

### Task 3: 补齐 pack_evidence 覆盖测试（15-25 分钟）

目的：把当前仓库里“已有但未纳入 git”的两条 pack_evidence 回归测试补齐，避免再出现“README 引用但 tar 缺失”。

**Files:**
- Create: `scripts/tests/test_pack_evidence_protocol_v2_sources.py`
- Create: `scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py`

**Step 1: 新增测试文件（直接从主工作区已有草稿拷贝即可）**

Run:
```bash
cp -v ../../scripts/tests/test_pack_evidence_protocol_v2_sources.py scripts/tests/
cp -v ../../scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py scripts/tests/
```

**Step 2: 跑测试（先确保 3 个 pack_evidence 测试都过）**

Run:
```bash
pytest -q scripts/tests/test_pack_evidence.py \
  scripts/tests/test_pack_evidence_follows_outputs_symlinks.py \
  scripts/tests/test_pack_evidence_protocol_v2_sources.py \
  scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py
```
Expected: PASS。

**Step 3: Commit（只提交测试文件）**

Run:
```bash
git add scripts/tests/test_pack_evidence_protocol_v2_sources.py \
  scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py
git commit -m "test(evidence): add pack_evidence coverage for v2 sources and gate viz"
```

---

### Task 4: 在仓库根目录重打离线包并回填 manifest（15-25 分钟）

**Files:**
- Create/Overwrite: `outputs/report_pack_2026-02-28.tar.gz`
- Modify: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

**Step 1: 生成离线包（在该 worktree 内执行即可）**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
```
Expected: 输出 `wrote ... (N files + manifest)`，且 tar 大小为百 MB 级（包含 mp4 与 cache）。

**Step 2: 用 tar 内 manifest 覆盖回填到 docs 快照**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
git add docs/report_pack/2026-02-27-v2/manifest_sha256.csv
git commit -m "docs(report_pack): refresh manifest snapshot from offline tar"
```

---

### Task 5: 抽查离线包覆盖关键引用（5-10 分钟）

**Step 1: 关键路径抽查（至少各命中 1 条）**

Run:
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/qualitative/planb_vs_baseline/.*step599\\.mp4\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/vggt_cache/.*/gt_cache\\.npz\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/cue_mining/.*/quality\\.json\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/protocol_v1/.*/stats/test_step0(199|599)\\.json\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/protocol_v2/.*/stats/test_step0(199|599)\\.json\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^outputs/report_pack/diagnostics/(temporal_diff_|tlpips_curve_)\" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n \"^notes/protocol_v2_(stage2_tradeoff_qual|tlpips_curve_diagnostics)\\.md\" | cat
```
Expected: 每条命令都有输出（说明 tar 覆盖 doc 引用的核心证据链）。

---

### Task 6: 推送/交付（按需要）（5 分钟）

**Step 1: 推送分支**

Run:
```bash
git push -u origin owner-b/protocol-v2-land-v2-pack
```

**Step 2: 在 PR 描述里写清“阻塞修复点”**

最小要点：
- 修复：worktree 下 `pack_evidence` 不递归 symlink outputs 子树导致 stats/mp4/cfg/vggt_cache/cue_mining 漏打
- 证据：离线包 + docs manifest 快照一致；新增 3 条 pack_evidence 回归测试
- 结论：stage‑2 mixed trend，不触发新增 full600
