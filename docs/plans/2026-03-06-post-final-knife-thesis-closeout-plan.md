# Post Final-Knife Thesis Closeout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `final knife = negative/mixed closed loop` 已经确认后，停止路线级扩张，把现有结果收敛成一套可直接用于论文写作、导师讨论和答辩的 thesis-grade closeout 包。

**Architecture:** 本轮不再新增训练路线，也不再重开 `oracle-weak` / `stage-2 gating` 搜索；只做文档化收口与证据冻结。执行顺序是：先做一份单文件权威讨论稿，再把它映射到论文章节、答辩材料和最终 evidence freeze，确保“主结果、创新点、负结果边界”三件事口径统一。

**Tech Stack:** Markdown, existing report-pack docs, existing notes/results under `outputs/`, `python3`, `rg`, `scripts/build_report_pack.py`, `scripts/pack_evidence.py`.

---

## Scope guardrails

- 不新增任何新的训练、评测协议或额外 seed。
- 不改现有指标口径，不改 `protocol_v2` 的历史结论。
- 主线硬结果始终是 `Plan-B`。
- `final knife` 固定为 `negative/mixed closed loop`。
- `oracle backgroundness weak-fusion` 固定为 `mixed evidence -> stop`。
- 所有新文档都必须坚持“能证明什么 / 不能证明什么”双栏口径，禁止把 mixed 结果包装成正结果。

---

### Task 0: Build one authoritative discussion file

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`
- Read: `notes/2026-03-06-final-knife-vggt-closed-loop.md`
- Read: `notes/2026-03-06-thuman4-oracle-weak-decision.md`

**Step 1: Draft the file with fixed sections**

The file must contain exactly these sections:
- `Current bottom line`
- `What is solidly positive`
- `What is innovative but bounded`
- `What was tested and closed negatively`
- `What should not be claimed`
- `Three-sentence discussion version`

**Step 2: Lock the route-level verdicts into the file**

The text must explicitly contain these verdict phrases:
- `Plan-B = mainline hard result`
- `final knife = negative/mixed closed loop`
- `oracle weak = mixed evidence -> stop`

**Step 3: Run a no-overclaim check**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md').read_text(encoding='utf-8')
required = [
    'Plan-B = mainline hard result',
    'final knife = negative/mixed closed loop',
    'oracle weak = mixed evidence -> stop',
]
for token in required:
    assert token in text, token
for bad in ['已证明 stage-2 全面有效', '稳定全面优于', '完整证明原版开题全部成立']:
    assert bad not in text, bad
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 1: Map the closeout story into thesis chapters

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/thesis-chapter-claim-map.md`
- Read: `4D-Reconstruction.md`
- Read: `4D-Reconstruction-v2.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md`

**Step 1: Create a chapter-by-chapter claim map**

Include at least these rows:
- `Introduction / Problem framing`
- `Method / Plan-B backbone`
- `VGGT soft-prior evidence`
- `Dynamic/static editable evidence`
- `Negative result and failure analysis`
- `Contribution and limitation summary`

Each row must have four columns:
- chapter or section
- allowed claim
- supporting files / assets
- forbidden overclaim

**Step 2: Ensure every row has a concrete asset path**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/thesis-chapter-claim-map.md').read_text(encoding='utf-8')
needles = ['outputs/', 'notes/', 'docs/report_pack/']
assert any(n in text for n in needles)
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 2: Prepare a defense asset checklist

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/defense-assets-checklist.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md`
- Read: `docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md`

**Step 1: List the minimum defense assets**

The checklist must include at least one item in each bucket:
- `main quantitative table`
- `dynamic/static demo`
- `VGGT cue / PCA / sparse correspondence visual`
- `negative result table`
- `limitations slide`

**Step 2: Add “what this asset proves” for each item**

Each checklist item must explicitly answer one sentence:
- `This asset proves ...`
- `This asset does not prove ...`

**Step 3: Verify the referenced asset paths exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
paths = [
    'docs/report_pack/2026-02-27-v2/scoreboard_full600_vs_v1.md',
    'docs/report_pack/2026-03-06-bishe-polish/edit-demo-brief.md',
    'docs/report_pack/2026-03-06-bishe-polish/vggt-soft-prior-brief.md',
    'notes/2026-03-06-final-knife-vggt-closed-loop.md',
]
missing = [p for p in paths if not Path(p).exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 3: Prepare advisor / reviewer Q&A

**Files:**
- Create: `docs/report_pack/2026-03-06-bishe-polish/defense-qa.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/original-proposal-alignment.md`
- Read: `notes/2026-03-06-final-knife-vggt-closed-loop.md`

**Step 1: Write the 8 hardest questions first**

The file must include concise answers to at least these questions:
- `你这是不是只是复现？`
- `为什么 stage-2 没跑成还说有创新？`
- `原版开题和现在差了多少？`
- `为什么 final knife 失败后还不继续重开？`
- `oracle weak 为什么 stop？`
- `你最硬的结果到底是哪一个？`
- `你最值得展示的 demo 是什么？`
- `你的边界和 limitation 是什么？`

**Step 2: Force every answer to use evidence-first wording**

Each answer must contain:
- one claim sentence
- one evidence sentence with file paths
- one boundary sentence beginning with `边界：`

**Step 3: Run a quick structure check**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
text = Path('docs/report_pack/2026-03-06-bishe-polish/defense-qa.md').read_text(encoding='utf-8')
for token in ['边界：', 'Plan-B', 'final knife', 'oracle weak']:
    assert token in text, token
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 4: Freeze the closeout evidence snapshot

**Files:**
- Modify: `docs/report_pack/2026-03-06-bishe-polish/README.md`
- Create/Modify: `docs/report_pack/2026-03-06-bishe-polish/evidence_freeze_sha256.txt`
- Read: `docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md`

**Step 1: Add one “frozen status” section to the README**

The section must state:
- no further route-level experiments are planned by default;
- current closeout packet is sufficient for thesis writing / discussion;
- re-opening experiments requires an explicit new question, not generic anxiety.

**Step 2: Rebuild and repack the final evidence packet**

Run:
```bash
python3 scripts/build_report_pack.py
python3 scripts/pack_evidence.py --out_tar outputs/report_pack_2026-03-06_bishe_final.tar.gz
sha256sum outputs/report_pack_2026-03-06_bishe_final.tar.gz | tee docs/report_pack/2026-03-06-bishe-polish/evidence_freeze_sha256.txt
```

Expected: final tar exists and SHA256 is recorded.

**Step 3: Verify the freeze artifacts exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    'docs/report_pack/2026-03-06-bishe-polish/README.md',
    'docs/report_pack/2026-03-06-bishe-polish/evidence_freeze_sha256.txt',
]
missing = [p for p in checks if not Path(p).exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

---

### Task 5: Final acceptance check

**Files:**
- Read: `docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/thesis-chapter-claim-map.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/defense-assets-checklist.md`
- Read: `docs/report_pack/2026-03-06-bishe-polish/defense-qa.md`

**Step 1: Re-answer the single closeout question**

After these files exist, you must be able to answer in one paragraph:

```text
主线结果、创新点、负结果边界、答辩口径，是否已经统一到一套可直接写论文和讨论的材料包中？
```

**Step 2: Verify the four closeout docs all exist**

Run:
```bash
python3 - <<'PY'
from pathlib import Path
checks = [
    'docs/report_pack/2026-03-06-bishe-polish/final-discussion-onefile.md',
    'docs/report_pack/2026-03-06-bishe-polish/thesis-chapter-claim-map.md',
    'docs/report_pack/2026-03-06-bishe-polish/defense-assets-checklist.md',
    'docs/report_pack/2026-03-06-bishe-polish/defense-qa.md',
]
missing = [p for p in checks if not Path(p).exists()]
assert not missing, missing
print('ok')
PY
```

Expected: prints `ok`.

**Step 3: Do not commit unless explicitly asked**

Expected: all edits remain uncommitted unless the user later requests a commit.
