# protocol_v2 Spatial Top-K Snapshots Post-Landing Follow-ups Implementation Plan (Owner A + Owner B)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 收口 `spatial metrics top-k frame snapshots` 的落地后续动作，并把 GitHub(HTTPS) 443 timeout 的规避/核验固化为可执行 checklist，避免再次阻塞 A->B 的合入与 PR 交付。

**Architecture:** 以最小改动闭环：补充 provenance 记录、补 `pack_evidence` 覆盖的回归单测、补 GitHub auth/连通性 gate（`gh` + `git` 两条链路）。不触碰训练/预算与既有证据链内容。

**Tech Stack:** `git`(https)、`gh`、`pytest`、`python3`。

---

## Current State (2026-02-28)

- A 交付分支：`owner-a/protocol-v2-spatial-metrics-topk-frames-code`
  - commit: `37d32266b37fdd9b29a538c7002709e9b5c25d60`
- B 集成分支：`owner-b/protocol-v2-land-v2-pack`
  - commits: `493cc5c`(导入 3 文件) -> `0356b7b`(README 入口) -> `75fe0a5`(manifest 回填)
- PR：`#1`（OPEN），head=`owner-b/protocol-v2-land-v2-pack`
- 既往阻塞：`git fetch/ls-remote` 访问 `github.com:443` 出现 `SSL connection timeout`；现已通过 PAT(classic)+`gh auth setup-git` 修复，但需要把“连通性 gate + 兜底路径”写成可执行步骤。

---

### Task 0: GitHub Connectivity Gate (Owner A + Owner B, Must)

**Files:** none

**Step 1: 确认 gh 登录状态**

Run:
```bash
gh auth status -h github.com
```

Expected: 显示已登录账号；且提示 git operations 已配置（credential helper 指向 `gh auth git-credential`）。

**Step 2: 验证 git HTTPS 能在 20s 内访问 GitHub**

Run:
```bash
timeout 20s git ls-remote https://github.com/RongYuzzz/4d-recon.git HEAD
```

Expected: 打印 1 行 `<sha>\tHEAD`，且命令 exit code 为 0。

**Step 3: 验证远端关键分支可见**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
timeout 30s git ls-remote --heads origin \
  owner-a/protocol-v2-spatial-metrics-topk-frames-code \
  owner-b/protocol-v2-land-v2-pack
```

Expected: 打印两行 `refs/heads/...`，且 sha 与上文一致。

**Step 4: 在 B worktree 验证可直接 fetch A 分支（消除 fallback 依赖）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
timeout 30s git fetch origin owner-a/protocol-v2-spatial-metrics-topk-frames-code
git log -1 --oneline FETCH_HEAD
```

Expected: `FETCH_HEAD` 指向 `37d3226...`。

**Step 5: 若仍失败（兜底路径，必须记录证据）**

Run:
```bash
# 用 GitHub API 读取分支 sha（不依赖 git 的 smart-http）
gh api repos/RongYuzzz/4d-recon/branches/owner-a%2Fprotocol-v2-spatial-metrics-topk-frames-code --jq .commit.sha

# 输出 curl 级别诊断（便于定位 DNS/IPv6/代理问题）
GIT_TRACE_CURL=1 GIT_CURL_VERBOSE=1 timeout 20s \
  git ls-remote https://github.com/RongYuzzz/4d-recon.git HEAD
```

Expected: API 能返回 sha；并把失败时的日志粘贴到 issue/PR comment 作为审计记录（不要“口头说已修复”）。

---

### Task B1: Record Provenance Mapping in PR (Owner B, Must)

**Files:** none (PR comment)

**Step 1: 证明 B 的导入提交与 A 的交付内容一致**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git diff 37d32266b37fdd9b29a538c7002709e9b5c25d60 493cc5cc0e21c5ec8148048a2d775b084a6b0951 -- \
  scripts/viz_spatial_metrics_topk_frames.py \
  scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py \
  notes/protocol_v2_spatial_metrics_topk_frames.md
```

Expected: 无输出（diff 为空）。

**Step 2: 在 PR#1 留 comment 记录 provenance**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-b-land-v2-pack
gh pr comment 1 --body $'spatial top-k snapshots provenance:\\n- Owner A branch: owner-a/protocol-v2-spatial-metrics-topk-frames-code @ 37d32266b37fdd9b29a538c7002709e9b5c25d60\\n- Owner B import commit: 493cc5cc0e21c5ec8148048a2d775b084a6b0951 (content-equivalent; diff is empty for the 3 files)\\n- Note: previous git fetch timeout on github.com:443 resolved via PAT(classic) + gh auth setup-git; Task0 connectivity gate added.'
```

Expected: PR comment 成功发布（URL 可在 `gh pr view 1` 的 comments 中查到）。

---

### Task B2: Add Pack Inclusion Regression Test for Spatial Top-K Pointers (Owner B, Recommended)

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

            # The note pointer that report-pack README links to.
            (root / "notes" / "protocol_v2_spatial_metrics_topk_frames.md").write_text(
                "# spatial top-k\n",
                encoding="utf-8",
            )

            # The offline pack pointer under outputs/report_pack/** must be present.
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
            self.assertEqual(proc.returncode, 0, msg=f"stderr:\\n{proc.stderr}")

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

**Step 3: 提交**

Run:
```bash
git add scripts/tests/test_pack_evidence_includes_spatial_metrics_topk_frames.py
git commit -m "test(pack): assert report-pack includes spatial top-k pointers"
git push
```

Expected: PR#1 自动更新包含该提交。

---

### Task A1: Add "How To Run" Usage Snippet to Note (Owner A, Recommended)

**Files:**
- Modify: `notes/protocol_v2_spatial_metrics_topk_frames.md`

**Step 1: 追加一个最小可复现命令段**

Append:
````markdown
## How to run

Example:
```bash
python3 scripts/viz_spatial_metrics_topk_frames.py \
  --renders_dir_a outputs/protocol_v2/selfcap_bar_8cam60f/planb_init_600/renders_test_step599 \
  --renders_dir_b outputs/protocol_v2/selfcap_bar_8cam60f/planb_feat_v2_full600/renders_test_step599 \
  --delta_csv outputs/report_pack/diagnostics/spatial_metrics_delta_planbfeat_minus_planb_test_step599.csv \
  --out_dir outputs/report_pack/diagnostics/spatial_metrics_topk_frames_planbfeat_minus_planb_test_step599 \
  --k 10 --resize_w 960 --quality 85
```

Expected:
- writes `frame_*.jpg` + `README.md` under `--out_dir`.
````

**Step 2: 复跑单测确保不破坏 contract**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-land-spatial-metrics-topk-code
pytest -q scripts/tests/test_viz_spatial_metrics_topk_frames_contract.py
```

Expected: `1 passed`。

**Step 3: 提交并推送**

Run:
```bash
git add notes/protocol_v2_spatial_metrics_topk_frames.md
git commit -m "docs(protocol_v2): add how-to-run for spatial top-k snapshots"
git push
```

Expected: 远端 A 分支包含该 doc commit；B 如需同步可直接 cherry-pick。

---

### Task B3: Decide on History Rewrite to Preserve A Original Commit (Owner B, Optional)

**Why:** 当前 B 分支的导入提交 `493cc5c` 与 A 的 `37d3226` 内容等价，但没有直接继承 A 的 sha（provenance 需要靠 PR comment 解释）。

**Option 1 (Recommended): Keep history, rely on PR comment**

Acceptance: Task B1 comment 完成即可。

**Option 2 (Risky): Rewrite history to cherry-pick A commit into B branch**

Constraints:
- 会改变 PR 的 commit graph，需要 `git push --force-with-lease`；
- 若多人已基于该分支工作，不建议执行。

High-level steps:
1) 创建备份分支（不可省略）
2) 新分支从导入前的 base 重新拼装 commits：先 cherry-pick `37d3226`，再 cherry-pick `0356b7b`、`75fe0a5`
3) `--force-with-lease` 推送并在 PR 说明“历史已重写”

Acceptance: PR 仍为 OPEN，且所有验证（pytest + pack + manifest_match）复跑通过。

---

### Task B4: Merge + Cleanup (Owner B, Must after PR approval)

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

**Step 3: 清理分支/工作区（避免 worktree 膨胀）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git worktree list
```

Manual:
- 删除不再需要的本地 worktree（先确认无未提交改动）
- 远端分支是否删除按仓库策略执行

---

### Task A2: Cleanup Owner A Worktree/Branch After Merge (Owner A, Recommended)

**Files:** none (repo hygiene)

**Step 1: 确认 PR#1 已合并**

Run:
```bash
gh pr view 1 --repo RongYuzzz/4d-recon --json number,state,headRefName,url
```

Expected: `state` 为 `MERGED` 或 `CLOSED`（按团队策略）。

**Step 2: 移除本地 A worktree（只在 clean 时执行）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git -C .worktrees/owner-a-land-spatial-metrics-topk-code status -sb
git worktree remove .worktrees/owner-a-land-spatial-metrics-topk-code
```

Expected: worktree 移除成功。

**Step 3: 删除 A 的远端分支（可选，按策略）**

Run:
```bash
cd /root/autodl-tmp/projects/4d-recon
git push origin --delete owner-a/protocol-v2-spatial-metrics-topk-frames-code
```

Expected: 远端分支删除成功；若团队要求保留审计分支，则跳过本步骤。
