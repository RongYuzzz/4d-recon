# Owner A Mainline Integration Implementation Plan

> 状态：已完成（存档）。不要再按本文执行；当前入口以 `README.md` / `notes/demo-runbook.md` 为准。

**Goal:** 把 A/B/C 已验收的成果合流到一个“可作为主阵地基线”的集成分支，并把入口脚本/文档/复现脚本默认值统一到可直接跑的状态（不依赖手工改路径）。

**Architecture:** 用 Git worktree 新建干净集成分支 `owner-a-20260224-mainline`，依次 merge `owner-a-20260223-exec`、`owner-b-20260224`、`owner-c-20260224`。在集成分支内统一 README 与 `scripts/run_mvp_repro.sh` 默认参数，并对 SelfCap 双适配脚本做“定版与去重策略”（默认推荐保留 B 脚本作为 Gate-1 canonical）。最后跑全量脚本测试（无需 pytest）+ `--dry-run` 复现检查；可选用 GPU0 做 10 steps 快速 smoke。

**Tech Stack:** Git worktrees, Bash, Python, FreeTimeGsVanilla `.venv`, OpenCV, NumPy

---

### Task A6: 创建干净集成 Worktree（不碰当前脏 `main` 目录）

**Files:**
- None (worktree only)

**Step 1: 创建集成 worktree + 分支**

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-a-20260224-mainline .worktrees/owner-a-20260224-mainline main
git -C .worktrees/owner-a-20260224-mainline status --porcelain=v1
```

Expected:
- `.worktrees/owner-a-20260224-mainline` 存在
- `status` 输出为空（干净）

**Step 2: 记录当前 `main` 脏状态（仅记录，不在此处处理）**

Run:
```bash
cd /root/projects/4d-recon
git status --porcelain=v1
```

Expected:
- 输出保存到终端日志（后续合并回 `main` 前用来对照）

---

### Task A7: 合流 A/B/C 分支（形成单一可用基线）

**Files:**
- Modify (merge): `README.md`
- Modify (merge): `third_party/FreeTimeGsVanilla/run_pipeline.sh`
- Create (merge): `scripts/adapt_hf_sample_to_freetime.py`
- Create (merge): `scripts/adapt_selfcap_release_to_freetime.py`
- Create (merge): `scripts/build_report_pack.py`
- Create (merge): `scripts/run_mvp_repro.sh`
- Create (merge): `scripts/run_gate0_smoke.sh`
- Create (merge): `scripts/run_gate1_smoke.sh`
- Create/Modify (merge): `scripts/tests/*`
- Modify (merge): `notes/*`

**Step 1: merge A 分支（入口脚本 + run_pipeline 透传 + 测试）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
git merge --no-ff owner-a-20260223-exec
```

Expected:
- merge 成功，无冲突

**Step 2: merge B 分支（SelfCap tarball adapter + Gate-1 记录 + 单测）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
git merge --no-ff owner-b-20260224
```

Expected:
- merge 成功，无冲突

**Step 3: merge C 分支（report-pack + T0 审计脚本/文档）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
git merge --no-ff owner-c-20260224
```

Expected:
- merge 成功，无冲突

**Step 4: 确认 worktree 干净**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
git status --porcelain=v1
```

Expected:
- 输出为空

---

### Task A8: 定版 SelfCap 入口（减少双维护）+ 统一 README/复现脚本默认值

**Files:**
- Modify: `README.md`
- Modify: `scripts/run_mvp_repro.sh`
- (Optional) Modify: `scripts/prepare_selfcap_for_freetime.py`（若决定保留则加“legacy”提示；若决定弃用则改名/迁移并更新 README）
- (Optional) Create: `scripts/tests/test_run_mvp_repro_defaults.py`

**Step 1: 决策记录（默认推荐）**

默认推荐定版：
- Gate-1 canonical：`scripts/adapt_selfcap_release_to_freetime.py`（直接吃 `bar-release.tar.gz`，不依赖系统 ffmpeg）
- `scripts/prepare_selfcap_for_freetime.py`：保留为 legacy（吃解压目录 + 可选 ffmpeg 抽帧），README 中明确“非主入口”

将该决策补充到 `notes/decision-log.md`（追加 2026-02-24 条目即可）。

**Step 2: README 同步 canonical 入口**

Edit: `README.md`
- 增加一段 SelfCap（Gate-1）推荐命令（与 B 的 `notes/selfcap_gate1_run.md` 对齐）：
  - 输入：`data/selfcap/bar-release.tar.gz`
  - 输出：`data/selfcap_bar_8cam60f`
  - 参数：`--camera_ids 02,03,04,05,06,07,08,09 --frame_start 0 --num_frames 60 --image_downscale 2`
- 将 `prepare_selfcap_for_freetime.py` 小节移动到“Legacy / Alternative”并标注依赖（`ffmpeg/ffprobe`）。

**Step 3: 修复 `run_mvp_repro.sh` 默认 tar 路径与自动适配**

Edit: `scripts/run_mvp_repro.sh`
- 将默认 `SELFCAP_TAR` 改为：`data/selfcap/bar-release.tar.gz`
- 增加默认输出目录（新参数或固定变量均可）：
  - `SELFCAP_OUT_DIR=data/selfcap_bar_8cam60f`
- 行为建议：
  - 若检测到 `$SELFCAP_OUT_DIR/triangulation` 不存在且脚本+tar 存在，则自动执行 adapter（等价于用户传 `--adapter-cmd`）
  - 保持 `--dry-run` 不执行，只打印命令

**Step 4 (Optional): 增加一个“默认值不回退”测试**

Create: `scripts/tests/test_run_mvp_repro_defaults.py`
- 只做静态检查（读取 `scripts/run_mvp_repro.sh` 文本），断言包含：
  - `data/selfcap/bar-release.tar.gz`
  - `adapt_selfcap_release_to_freetime.py`

Run:
```bash
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_run_mvp_repro_defaults.py
```

Expected:
- `PASS: ...`

**Step 5: 提交文档与脚本改动**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
git add README.md notes/decision-log.md scripts/run_mvp_repro.sh scripts/tests/test_run_mvp_repro_defaults.py 2>/dev/null || true
git commit -m "docs: standardize SelfCap canonical adapter + fix repro defaults"
```

Expected:
- 新增 1 个 commit（仅代码/文档，不含 data/outputs）

---

### Task A9: 全量脚本测试 + dry-run 复现检查（CPU 为主，可并行于他人跑实验）

**Files:**
- None

**Step 1: 跑所有 tests（按脚本直接运行，不依赖 pytest）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python

$PY scripts/tests/test_export_triangulation_adapter.py
$PY scripts/tests/test_run_pipeline_env_flags.py
$PY scripts/tests/test_run_pipeline_extra_train_args.py
$PY scripts/tests/test_adapt_hf_sample.py
$PY scripts/tests/test_adapt_hf_sample_per_frame_sparse.py
$PY scripts/tests/test_run_gate1_smoke_frame_count.py
$PY scripts/tests/test_t0_config_flags.py
$PY scripts/tests/test_selfcap_parsers.py
```

Expected:
- 全部 `PASS`

**Step 2: Shell 语法检查**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
bash -n scripts/run_gate0_smoke.sh
bash -n scripts/run_gate1_smoke.sh
bash -n scripts/run_mvp_repro.sh
bash -n third_party/FreeTimeGsVanilla/run_pipeline.sh
```

Expected:
- 全部退出码为 0

**Step 3: `run_mvp_repro.sh` dry-run**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
bash scripts/run_mvp_repro.sh --dry-run --gpu 0 --max-steps 10 --skip-gate0
```

Expected:
- 打印 adapter + trainer 命令（不实际执行），退出码为 0

**Step 4 (Optional): GPU0 10 steps 快速 smoke（只在有空时做）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-mainline
MAX_STEPS=10 CUDA_VISIBLE_DEVICES=0 bash scripts/run_mvp_repro.sh --skip-gate0
```

Expected:
- 产物目录出现 `outputs/` 下新 run 的 `stats/val_step*.json` 与 `videos/*.mp4`（不要求指标好看）

---

### Task A10: 合并集成分支回 `main`（与团队约定窗口，避免相互踩）

**Files:**
- Git branch update only

**Step 1: 先把当前 `/root/projects/4d-recon` 的脏改动做非破坏性保护**

Run:
```bash
cd /root/projects/4d-recon
git status --porcelain=v1
git stash push -u -m "wip(main): before merging owner-a-20260224-mainline"
git status --porcelain=v1
```

Expected:
- 第二次 `status` 输出为空（main 目录干净）

**Step 2: 合并集成分支**

Run:
```bash
cd /root/projects/4d-recon
git merge --ff-only owner-a-20260224-mainline
git log -5 --oneline
```

Expected:
- `main` 前进到包含 A/B/C 的提交

**Step 3: 在 `main` 上复跑最小 tests（保证主阵地可用）**

Run:
```bash
cd /root/projects/4d-recon
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_export_triangulation_adapter.py
$PY scripts/tests/test_selfcap_parsers.py
$PY scripts/tests/test_t0_config_flags.py
```

Expected:
- 全部 `PASS`

**Step 4: 评估是否需要 `stash pop`**

说明：
- 若 stash 内容是“过时/重复”的旧文件（例如早期的 SelfCap 适配脚本副本），建议不要 pop；改为手动 cherry-pick 需要的文件后丢弃 stash。
- 若 stash 是你个人临时改动且仍需要，才执行 `git stash pop` 并解决冲突。
