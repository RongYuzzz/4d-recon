# protocol_v2 Publish Landed Pack Fixes + PR to main Implementation Plan (Owner B / GPU1)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `owner-b/protocol-v2-land-v2-pack` 的落地修复（`pack_evidence` symlink 递归 + 回归测试 + stage‑2 诊断 + 离线包/manifest 一致性）**稳定发布**：完成 `README` 入口补齐、重打离线包并回填 manifest、推送远端、对 `main` 建 PR（或在需要时先推 base 分支）。

**Architecture:** 以 worktree `.worktrees/owner-b-land-v2-pack` 为 source‑of‑truth；任何改动（包括 `docs/report_pack/.../README.md`）都会影响 tar/manifest，因此按“改 docs → 重打 tar → 回填 manifest → `manifest_match` 校验”的顺序闭环；推送若受网络影响，提供 `git bundle`/`format-patch` 作为离线交付兜底。

**Tech Stack:** `git`、`python3`、`pytest`、`tar`、`rg`。（GPU1 不强依赖，本计划以发布闭环为主。）

---

## Constraints / Invariants（必须遵守）

- 不新增 full600；本计划只做发布/文档/打包闭环。
- tarball 不进 git：`outputs/report_pack_2026-02-28.tar.gz` 仅作为可重复生成的离线产物；git 中只提交 `docs/report_pack/.../manifest_sha256.csv` 快照。
- 任何路径引用必须能在 tar 内被命中（README/notes 引用路径即证据链的一部分）。

---

### Task 0: Preflight（5-10 分钟）

**Step 1: 进入 worktree 并确认分支状态**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
git status -sb --porcelain
git rev-parse --abbrev-ref HEAD
```
Expected:
- 分支为 `owner-b/protocol-v2-land-v2-pack`
- 工作区 clean

**Step 2: 关键验证（测试 + manifest_match）**

Run:
```bash
pytest -q scripts/tests/test_pack_evidence.py \
  scripts/tests/test_pack_evidence_follows_outputs_symlinks.py \
  scripts/tests/test_pack_evidence_protocol_v2_sources.py \
  scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py

tmp=$(mktemp)
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > "$tmp"
cmp -s "$tmp" docs/report_pack/2026-02-27-v2/manifest_sha256.csv && echo "manifest_match: yes" || echo "manifest_match: no"
rm -f "$tmp"
```
Expected: `manifest_match: yes`。

---

### Task 1: README 入口补齐（spatial metrics）（10-20 分钟）

**动机**：目前 stage‑2 已有 temporal diff + tLPIPS 曲线入口，但 spatial metrics（per‑frame GT vs Pred）若不在 `docs/report_pack/.../README.md` 出现，容易被遗漏。

**Files:**
- Modify: `docs/report_pack/2026-02-27-v2/README.md`

**Step 1: 在 “Stage‑2 trade-off diagnosis” 区域追加一小段指针**

建议最小新增（不要长文）：
- `notes/protocol_v2_spatial_metrics_diagnostics.md`
- `outputs/report_pack/diagnostics/spatial_metrics_*`（5 个文件）
- 一句话口径：`PSNR` 全帧提升，但 `MAE` 局部（52-59）劣化；与 `41->42` 时序锚点互补

**Step 2: commit（只提交 README）**

Run:
```bash
git add docs/report_pack/2026-02-27-v2/README.md
git commit -m "docs(report_pack): add spatial metrics diagnostics pointers"
```

---

### Task 2: 重打离线包 + 回填 manifest（必做）（10-20 分钟）

**原因**：README 变更会导致 tar/manifest 快照变化，必须闭环到 `manifest_match: yes`。

**Files:**
- Create/Overwrite: `outputs/report_pack_2026-02-28.tar.gz`
- Modify: `docs/report_pack/2026-02-27-v2/manifest_sha256.csv`

**Step 1: 生成 tar**

Run:
```bash
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
```
Expected: 输出类似 `(... files + manifest)`。

**Step 2: 回填 manifest 快照并 commit**

Run:
```bash
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
git add docs/report_pack/2026-02-27-v2/manifest_sha256.csv
git commit -m "docs(report_pack): refresh manifest snapshot from offline tar"
```

**Step 3: 校验 manifest_match**

Run:
```bash
tmp=$(mktemp)
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > "$tmp"
cmp -s "$tmp" docs/report_pack/2026-02-27-v2/manifest_sha256.csv && echo "manifest_match: yes" || echo "manifest_match: no"
rm -f "$tmp"
```
Expected: `manifest_match: yes`。

---

### Task 3: tar 抽查关键证据链（5-10 分钟）

Run:
```bash
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^outputs/qualitative/planb_vs_baseline/.*step599\\.mp4$" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^outputs/vggt_cache/.*/gt_cache\\.npz$" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^outputs/cue_mining/.*/quality\\.json$" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^outputs/protocol_v1/.*/stats/test_step0(199|599)\\.json$" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^outputs/protocol_v2/.*/stats/test_step0(199|599)\\.json$" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^outputs/report_pack/diagnostics/(temporal_diff_|tlpips_curve_|spatial_metrics_)" | head
tar -tzf outputs/report_pack_2026-02-28.tar.gz | rg -n "^notes/protocol_v2_(stage2_tradeoff_qual|tlpips_curve_diagnostics|spatial_metrics_diagnostics)\\.md$" | cat
```
Expected: 每类至少命中 1 条。

---

### Task 4: 推送远端（含网络失败兜底）（5-15 分钟）

**Step 1: 正常 push**

Run:
```bash
git push -u origin owner-b/protocol-v2-land-v2-pack
```

**Step 2（兜底）：若 GitHub 网络超时，生成离线交付物**

Run:
```bash
# 1) 单文件 bundle（可离线传输给他人再 push）
git bundle create outputs/owner-b_protocol-v2-land-v2-pack.bundle origin/main..HEAD

# 2) 或生成 format-patch（可邮件/IM 传输）
mkdir -p outputs/patches_owner-b_protocol-v2-land-v2-pack
git format-patch -o outputs/patches_owner-b_protocol-v2-land-v2-pack origin/main..HEAD
```
Acceptance: bundle/patch 生成成功且可见。

---

### Task 5: 建 PR（base=main）（5-15 分钟）

**推荐**：直接对 `main` 建 PR（当前远端无 `owner-b/c2-full600-integration-livews`）。

Option A（若 `gh` 可用）：
```bash
gh pr create \
  --base main \
  --head owner-b/protocol-v2-land-v2-pack \
  --title "protocol_v2: land pack_evidence symlink fix + stage2 diagnostics + offline pack closure" \
  --body "Key changes:\n- fix: pack_evidence follows outputs/* symlink dirs (worktree-safe)\n- tests: add coverage for v2 sources + gate_framediff\n- diagnostics: temporal diff / tLPIPS curve / spatial metrics pointers\n- offline: repack tar and refresh manifest snapshot (manifest_match: yes)\n\nVerify:\n- pytest -q scripts/tests/test_pack_evidence*.py\n- python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz\n- cmp docs manifest with tar manifest\n"
```

Option B（若必须保留原 base 分支）：先推 base，再对该 base 建 PR：
```bash
git push -u origin owner-b/c2-full600-integration-livews:refs/heads/owner-b/c2-full600-integration-livews
```

---

### Task 6: PR 验收口径（5 分钟）

在 PR 描述里明确三点（避免争议）：
- 预算纪律：不新增 full600，本 PR 仅打包/诊断/证据链修复。
- 可审计性：README/notes 引用路径均在 tar 内命中；`manifest_match: yes`。
- 可复现：给出 3 条命令（`pytest` / `pack_evidence` / `manifest_match` 校验）。

