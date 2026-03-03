# protocol_v2 Spatial Top-K Snapshots Post-Landing Follow-ups (Owner B) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Owner B 侧把 `spatial metrics top-k frame snapshots` 的 PR 交付做成“可审计、可复现、可持续”：固化 GitHub(HTTPS) 连通性 gate（避免 443 timeout 阻塞 A->B 取分支）、在 PR 里记录 provenance（A sha ↔ B 导入 sha）、补 pack 入口回归单测（推荐），并在评审通过后合并与清理。

**Architecture:** 最小改动原则：不重写历史默认方案为“PR comment 记录 provenance”；若强需要保留 A 的原始 commit graph，提供可选的 rewrite 方案（高风险、需要 force push）。

**Tech Stack:** `git`(https)、`gh`、`pytest`、`python3`。

---

## Parallelism Notes

- 可立即并行执行（不依赖 A 的后续动作）：Task B0、Task B1、Task B2
- 依赖评审/merge：Task B4
- 可选高风险动作：Task B3（只有在团队明确要求时执行）

---

## Current State (2026-02-28)

- B 分支：`owner-b/protocol-v2-land-v2-pack`
  - HEAD: `75fe0a540c5882309cadda6ed78c49fe01aa7d0d`
  - 导入 3 文件的提交：`493cc5cc0e21c5ec8148048a2d775b084a6b0951`
- A 分支：`owner-a/protocol-v2-spatial-metrics-topk-frames-code`
  - commit: `37d32266b37fdd9b29a538c7002709e9b5c25d60`
- PR：`#1`（OPEN），head=`owner-b/protocol-v2-land-v2-pack`
- 既往阻塞：`git fetch origin owner-a/...` 曾因 `github.com:443` timeout 失败，导致不得不使用本地 fallback；现已配置 PAT(classic)+`gh auth setup-git`，仍需用 gate 固化。

---

### Task B0: GitHub Connectivity Gate (Must, 2-5 min)

**Files:** none

**Step 1: 确认 gh 登录状态**

Run:
```bash
gh auth status -h github.com
```

Expected: 显示已登录账号；并提示 git operations 已配置。

**Step 2: 验证 git HTTPS 能在 20s 内访问 GitHub**

Run:
```bash
timeout 20s git ls-remote https://github.com/RongYuzzz/4d-recon.git HEAD
```

Expected: 打印 1 行 `<sha>\tHEAD`，且 exit code 为 0。

**Step 3: 在 B worktree 验证可直接 fetch A 分支**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
timeout 30s git fetch origin owner-a/protocol-v2-spatial-metrics-topk-frames-code
git log -1 --oneline FETCH_HEAD
```

Expected: `FETCH_HEAD` 指向 `37d3226...`。

**Step 4: 若仍失败（兜底，必须记录证据）**

Run:
```bash
gh api repos/RongYuzzz/4d-recon/branches/owner-a%2Fprotocol-v2-spatial-metrics-topk-frames-code --jq .commit.sha
GIT_TRACE_CURL=1 GIT_CURL_VERBOSE=1 timeout 20s \
  git ls-remote https://github.com/RongYuzzz/4d-recon.git HEAD
```

Expected: API 能返回 sha；并把失败日志粘贴到 PR comment 作为审计记录。

---

### Task B1: Record Provenance Mapping in PR (Must, 2-5 min)

**Files:** none (PR comment)

**Step 1: 证明 B 的导入提交与 A 的交付内容一致（diff 为空）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git diff 37d32266b37fdd9b29a538c7002709e9b5c25d60 493cc5cc0e21c5ec8148048a2d775b084a6b0951 -- \
  scripts/viz_spatial_metrics_topk_frames.py \
  scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py \
  notes/protocol_v2_spatial_metrics_topk_frames.md
```

Expected: 无输出（diff 为空）。

**Step 2: 在 PR#1 留 comment 记录 provenance + 连通性修复结论**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
gh pr comment 1 --body $'spatial top-k snapshots provenance:\\n- Owner A branch: owner-a/protocol-v2-spatial-metrics-topk-frames-code @ 37d32266b37fdd9b29a538c7002709e9b5c25d60\\n- Owner B import commit: 493cc5cc0e21c5ec8148048a2d775b084a6b0951 (content-equivalent; diff is empty for the 3 files)\\n- Ops: previous git fetch timeout on github.com:443 resolved via PAT(classic) + gh auth setup-git; connectivity gate added (Task B0).'
```

Expected: PR comment 成功发布。

---

### Task B2: Add Pack Inclusion Regression Test for Spatial Top-K Pointers (Recommended, 5-10 min)

**Files:**
- Create: `scripts/tests/test_pack_evidence_includes_spatial_metrics_topk_frames.py`

**Step 1: 写单测（最小结构即可）**

Create:
```python
from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "pack_evidence.py"


class PackEvidenceIncludesSpatialTopKFramesTests(unittest.TestCase):
    def test_pack_should_include_spatial_metrics_topk_frames_note_and_readme(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pack_evidence_spatial_topk_", dir=REPO_ROOT) as td:
            root = Path(td)
            (root / "README.md").write_text("demo\n", encoding="utf-8")
            (root / "notes").mkdir(parents=True, exist_ok=True)
            (root / "notes" / "demo-runbook.md").write_text("# runbook\n", encoding="utf-8")

            (root / "notes" / "protocol_v2_spatial_metrics_topk_frames.md").write_text(
                "# spatial top-k\n",
                encoding="utf-8",
            )

            out_readme = (
                root
                / "outputs"
                / "report_pack"
                / "diagnostics"
                / "spatial_metrics_topk_frames_demo"
                / "README.md"
            )
            out_readme.parent.mkdir(parents=True, exist_ok=True)
            out_readme.write_text("# top-k frames\n", encoding="utf-8")

            out_tar = root / "pack.tar.gz"
            cmd = [
                sys.executable,
                str(SCRIPT),
                "--repo_root",
                str(root),
                "--out_tar",
                str(out_tar),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\n{proc.stderr}")

            with tarfile.open(out_tar, "r:gz") as tf:
                names = set(tf.getnames())

            must_have = {
                "notes/protocol_v2_spatial_metrics_topk_frames.md",
                "outputs/report_pack/diagnostics/spatial_metrics_topk_frames_demo/README.md",
            }
            for name in must_have:
                self.assertIn(name, names)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: 运行单测**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
pytest -q scripts/tests/test_pack_evidence_includes_spatial_metrics_topk_frames.py
```

Expected: `1 passed`。

**Step 3: 提交并 push**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
git add scripts/tests/test_pack_evidence_includes_spatial_metrics_topk_frames.py
git commit -m "test(pack): assert report-pack includes spatial top-k pointers"
git push
```

Expected: PR#1 自动更新包含该提交。

---

### Task B3: (Optional, Risky) Rewrite History to Preserve A Original Commit

**Why:** 当前 B 的导入提交与 A 的 commit 内容等价，但 graph 不包含 A 的原始 sha；若审计/协作强要求“保留 A sha 进入主分支历史”，才考虑此任务。

**Constraints:**
- 需要 `git push --force-with-lease`
- 可能影响其他人基于该分支的工作

**High-level steps:**
1) 创建备份分支（不可省略）
2) 新分支从导入前 base 重新拼装：先 `cherry-pick 37d3226`，再 `cherry-pick 0356b7b`、`75fe0a5`
3) 复跑验证（pytest + pack + manifest_match）
4) `--force-with-lease` 推送并在 PR 说明“历史已重写”

Acceptance: PR 仍为 OPEN 且验证全部 PASS。

---

### Task B4: Merge + Cleanup (Must after PR approval)

**Files:** none (repo hygiene)

**Step 1: 合并前复核**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
pytest -q scripts/tests/test_pack_evidence.py \
  scripts/tests/test_pack_evidence_follows_outputs_symlinks.py \
  scripts/tests/test_pack_evidence_protocol_v2_sources.py \
  scripts/tests/test_pack_evidence_includes_gate_framediff_viz.py
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-02-28.tar.gz
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv > docs/report_pack/2026-02-27-v2/manifest_sha256.csv
tar -xOzf outputs/report_pack_2026-02-28.tar.gz manifest_sha256.csv | cmp -s - docs/report_pack/2026-02-27-v2/manifest_sha256.csv \
  && echo "manifest_match: yes" || echo "manifest_match: no"
```

Expected: pytest 全部 PASS，且 `manifest_match: yes`。

**Step 2: 合并 PR#1（按团队规范执行）**

Run (example):
```bash
gh pr merge 1 --merge
```

Expected: PR state 变为 MERGED。

**Step 3: 清理本地 worktree（先确认无未提交改动）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git worktree list
```

Manual:
- 移除不再需要的 worktree
- 远端分支删除按仓库策略执行

