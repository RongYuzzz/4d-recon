# Bishe Final Innovation Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不再冒险扩张高风险训练主线的前提下，把当前项目收敛成一个“工作量饱满、创新点闭环更完整、并且尽量对齐原版开题路线”的最终交付包。

**Architecture:** 以“低风险补闭环”为原则，不新增大规模 mainline 训练，不再追求翻盘式数值提升；而是围绕原版开题的两条已基本落地的支线——`VGGT` 线索提取/可解释性 与 动静解耦/编辑演示——做最后一轮包装与收口。最终交付重点不是新指标，而是一个可直接放进毕设/答辩的单一证据入口：能清楚回答“原版开题做了什么、哪些做成了、哪些做到边界、创新性具体体现在哪里”。

**Tech Stack:** Markdown docs, existing experiment outputs, `ffmpeg` for frame extraction, existing report-pack assets, Python path checks.

---

## Scope and decision rules

- **In scope:**
  - 打磨“动静解耦 + 编辑演示”证据包；
  - 把 `VGGT cue / PCA / sparse correspondence` 收成一个自洽的 soft-prior 章节；
  - 新增“原版开题路线 vs 当前落地状态”的对齐表；
  - 生成一个可以直接给导师/答辩使用的单一入口文档。
- **Out of scope:**
  - 不新增大规模 `full600`/`smoke200` 搜索；
  - 不重开 `oracle-weak` 路线；
  - 不把 stage-2 mixed/trade-off 写成稳定正结果；
  - 不做新的 object inpainting 系统；
  - 不 `git commit`（除非用户后续明确要求）。

Working rule:
- 所有新增叙述必须严格区分 **done / partial / exploratory / not closed**。
- 所有“创新性”表述必须能回指到原版开题 `4D-Reconstruction.md` 的具体路线项。

---

### Task 0: Freeze scope and verify current evidence roots

**Files:**
- Read: `4D-Reconstruction.md`
- Read: `4D-Reconstruction-v2.md`
- Read: `docs/report_pack/2026-02-27-v2/README.md`
- Read: `notes/openproposal_phase5_edit_demo.md`
- Read: `notes/protocol_v2_vggt_cue_viz.md`
- Read: `notes/protocol_v2_vggt_feature_pca.md`
- Read: `notes/protocol_v2_sparse_corr_viz.md`

**Step 1: Verify the original-vs-v2 route anchors exist**

Run:
```bash
[ -f 4D-Reconstruction.md ]
[ -f 4D-Reconstruction-v2.md ]
[ -f docs/report_pack/2026-02-27-v2/README.md ]
```

Expected: all three files exist; these are the canonical route definitions for the final alignment write-up.

**Step 2: Verify the current polish will be built from existing artifacts, not from hypothetical future runs**

Run:
```bash
[ -f notes/openproposal_phase5_edit_demo.md ]
[ -f notes/protocol_v2_vggt_cue_viz.md ]
[ -f notes/protocol_v2_vggt_feature_pca.md ]
[ -f notes/protocol_v2_sparse_corr_viz.md ]
```

Expected: all four files exist. If any are missing, stop and restore the corresponding note path first.

**Step 3: Verify the key media artifacts exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4'),
    Path('outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4'),
    Path('outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4'),
    Path('outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/quality.json'),
    Path('outputs/cue_mining/selfcap_bar_8cam60f_vggt_probe/viz/grid_frame000000.jpg'),
    Path('outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/viz_pca/grid_pca_frame000000.jpg'),
    Path('outputs/correspondences/selfcap_bar_8cam60f_tokenproj_temporal_topk_v1/viz/token_top20_cam02_frame000000_to_000001.jpg'),
]
missing = [str(p) for p in checks if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`. If not, do not continue to packaging.

---

### Task 1: Build a polished edit-demo packet that aligns with the original proposal’s “可编辑性” claim

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
- Create: `outputs/qualitative_local/bishe_edit_demo_frames/`
- Read: `notes/openproposal_phase5_edit_demo.md`
- Read: `notes/protocol_v2_static_dynamic_tau.md`
- Read: `notes/qna.md`

**Step 1: Create a clean frame export directory**

Run:
```bash
mkdir -p outputs/qualitative_local/bishe_edit_demo_frames
```

Expected: the directory exists and is ready to hold still frames.

**Step 2: Extract representative stills from static/dynamic/full videos**

Run:
```bash
ffmpeg -y -i outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4 \
  -vf "select='eq(n,0)+eq(n,15)+eq(n,30)'" -vsync vfr \
  outputs/qualitative_local/bishe_edit_demo_frames/static_%03d.jpg

ffmpeg -y -i outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4 \
  -vf "select='eq(n,0)+eq(n,15)+eq(n,30)'" -vsync vfr \
  outputs/qualitative_local/bishe_edit_demo_frames/dynamic_%03d.jpg

ffmpeg -y -i outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4 \
  -vf "select='eq(n,0)+eq(n,15)+eq(n,30)'" -vsync vfr \
  outputs/qualitative_local/bishe_edit_demo_frames/full_%03d.jpg
```

Expected: 9 jpg files are created under `outputs/qualitative_local/bishe_edit_demo_frames/`.

**Step 3: Verify the extracted frame packet exists**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
root = Path('outputs/qualitative_local/bishe_edit_demo_frames')
expected = [
    root / 'static_001.jpg', root / 'static_002.jpg', root / 'static_003.jpg',
    root / 'dynamic_001.jpg', root / 'dynamic_002.jpg', root / 'dynamic_003.jpg',
    root / 'full_001.jpg', root / 'full_002.jpg', root / 'full_003.jpg',
]
missing = [str(p) for p in expected if not p.exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

**Step 4: Write a concise edit-demo brief that is faithful to what actually exists**

Create `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md` with these sections:
- `What is shown`
- `Why this aligns with the original proposal`
- `What the demo is and is not`
- `Deliverable paths`
- `Failure boundary`

Required content constraints:
- Must explicitly say the current demo is **dynamic/static filtering-based editable evidence**, not full object inpainting.
- Must cite the limitation already recorded in `notes/openproposal_phase5_edit_demo.md`.
- Must map this demo back to the original proposal’s “动静解耦 / 物体移除” promise.

Suggested wording snippet to include:
```md
当前交付的是“基于动静分层导出的可编辑演示雏形”：它已经能够展示 dynamic/static 分离与 removal-style filtering 的可视效果，但仍不是完整的 object inpainting/editing system。
```

**Step 5: Verify the brief includes the required guardrail terms**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md').read_text(encoding='utf-8')
for needle in ['动静解耦', 'filtering', 'not inpainting', '物体移除', 'Failure boundary']:
    assert needle in text, needle
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 2: Consolidate the VGGT soft-prior story into one thesis-ready packet

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`
- Read: `notes/protocol_v2_vggt_cue_viz.md`
- Read: `notes/protocol_v2_vggt_feature_pca.md`
- Read: `notes/protocol_v2_sparse_corr_viz.md`
- Read: `4D-Reconstruction.md`

**Step 1: Write a single self-contained soft-prior brief**

Create `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md` with this structure:
- `Original proposal target`
- `What was actually implemented`
- `Evidence 1: cue / pseudo mask`
- `Evidence 2: token_proj PCA`
- `Evidence 3: sparse correspondence visualization`
- `What this proves`
- `What it does not prove`

Required constraints:
- It must explicitly connect back to the original proposal’s first two route items in `4D-Reconstruction.md`.
- It must not claim that the stage-2 optimization is stably effective.
- It must explicitly distinguish **interpretability evidence** from **optimization gain evidence**.

**Step 2: Add a three-level conclusion inside the brief**

The brief must contain a short block like:
```md
- 已完成：VGGT 线索提取、可视化与稀疏对应示意。
- 部分完成：soft prior 注入与 stage-2 训练闭环。
- 尚未闭环：把 VGGT 约束稳定转化为全指标收益。
```

**Step 3: Verify the brief contains all three evidence types**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md').read_text(encoding='utf-8')
for needle in ['pseudo mask', 'PCA', 'sparse correspondence', 'What it does not prove']:
    assert needle in text, needle
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 3: Build an original-proposal alignment table for objective self-evaluation

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `4D-Reconstruction.md`
- Read: `4D-Reconstruction-v2.md`
- Read: `docs/report_pack/2026-02-27-v2/README.md`
- Read: `notes/2026-03-06-thuman4-oracle-weak-decision.md`

**Step 1: Create a 3-column alignment table**

Create `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md` with a table like:
```md
| Original route item | Current status | Evidence |
|---|---|---|
| VGGT latent cue mining | Done | ... |
| Attention/correspondence guided optimization | Partial / exploratory | ... |
| Dynamic-static decoupling + removal demo | Partial but demonstrable | ... |
| Strong benchmark superiority claim | Not achieved / narrowed in v2 | ... |
```

Constraints:
- Status values must come from the closed set: `Done`, `Partial`, `Exploratory`, `Not achieved`, `Superseded by v2 narrowing`.
- Every row must cite at least one exact evidence file path.
- The table must explicitly explain why the project still counts as “工作量饱满 + 有一点创新性” **without** pretending the original strongest claims were all proven.

**Step 2: Add a bottom-line self-evaluation paragraph**

The paragraph must answer:
- What from the original proposal was truly landed?
- What was narrowed by v2?
- Why the current package is still defensible as a strong undergraduate thesis?

**Step 3: Verify every evidence path in the table exists**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
note = Path('docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md')
missing = []
for line in note.read_text(encoding='utf-8').splitlines():
    if '`' not in line:
        continue
    for part in line.split('`')[1::2]:
        if part.startswith('outputs/') or part.startswith('notes/') or part.startswith('docs/') or part.startswith('4D-Reconstruction'):
            p = Path(part)
            if ('...' in part) or ('*.jpg' in part) or ('*.png' in part):
                continue
            if not p.exists():
                missing.append(part)
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 4: Create one final entrypoint for advisor / defense use

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`

**Step 1: Write the single-entry README**

Create `docs/report_pack/2026-03-06-bishe-polish/README.md` that answers, in this order:
1. `What is the mainline result?`
2. `What is the innovation story?`
3. `What is the strongest demo?`
4. `What is the honest limitation?`
5. `Which 3 files should a busy reviewer open first?`

Required answer shape:
- mainline result must point to `Plan-B only` / stage-1 hard evidence;
- innovation story must point to `VGGT soft prior + dynamic/static editable evidence`;
- honest limitation must say stage-2 has not become a stable positive line.

**Step 2: Add a “three files first” section**

It must recommend exactly these three files:
- `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
- `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`

**Step 3: Verify the README does not overclaim**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/README.md').read_text(encoding='utf-8')
for bad in ['稳定全面优于', '已证明 stage-2 有效', '完整 object editing system']:
    assert bad not in text, bad
for good in ['Plan-B', 'soft prior', 'mixed/trade-off', 'dynamic/static']:
    assert good in text, good
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 5: Optional one-shot peer review (narrow scope, not open-ended)

**Files:**
- Read: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`

**Step 1: Only if time allows, ask one peer / expert one narrow question**

Suggested prompt focus:
```text
在“优秀毕设：工作量饱满 + 有一点创新性”的口径下，这套最终包是否已经足够稳？如果还差最后一刀，你建议我优先补‘编辑演示说服力’还是‘VGGT soft-prior 章节说服力’？
```

Expected: this is a narrow calibration review, not a new broad scientific diagnosis session.

**Step 2: Do not reopen experimental scope based on generic feedback**

Expected: unless the feedback points to a trivial packaging fix, do not reopen training or route-level decisions.

---

### Task 6: Final acceptance check

**Files:**
- Read: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`

**Step 1: Verify all new deliverables exist**

Run:
```bash
[ -f docs/report_pack/2026-03-06-bishe-polish/README.md ]
[ -f docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md ]
[ -f docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md ]
[ -f docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md ]
```

Expected: all four files exist.

**Step 2: Verify the final package answers the three defense-critical questions**

Use this checklist:
- Can a reviewer see that the project did more than a baseline reproduction?
- Can a reviewer identify at least one concrete innovation thread that is actually landed?
- Can a reviewer understand the honest boundary of stage-2 without feeling misled?

Expected: all three answers should be “yes”.

**Step 3: Commit nothing**

Expected: do not `git commit` unless the user explicitly asks.

