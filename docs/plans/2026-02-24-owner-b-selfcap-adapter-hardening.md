# SelfCap Tarball Adapter Hardening Implementation Plan (Owner B)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `scripts/adapt_selfcap_release_to_freetime.py` 打磨成可长期维护的“SelfCap Gate-1 canonical 数据入口”：可重复运行不污染输出目录、可在无视频/无解码环境下导出 tri+sparse（用于快速链路验证）、并补齐相机畸变模型支持与对应测试。

**Architecture:** 保持脚本现有“直接吃 `bar-release.tar.gz`”的优势，在 CLI 层新增 `--overwrite` 与 `--no_images`（+ 必要的尺寸参数），并在 `write_colmap_sparse0()` 内按 intri.yml 的 `dist_*` 自动选择 `PINHOLE/OPENCV`。所有改动走 TDD：先写脚本级/函数级单测（不依赖真实大 tarball、不依赖 mp4），再最小实现，最后在 GPU1 上可选做一次 10 steps sanity（非必须）。

**Tech Stack:** Python, `tarfile`, `unittest`, NumPy, OpenCV, FreeTimeGsVanilla `datasets/read_write_model.py`

---

### Task B6: 创建隔离分支 Worktree（避免影响当前可用分支）

**Files:**
- None (worktree only)

**Step 1: 创建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git worktree add -b owner-b-20260224-selfcap-hardening .worktrees/owner-b-20260224-selfcap-hardening owner-b-20260224
cd .worktrees/owner-b-20260224-selfcap-hardening
git status --porcelain=v1
```

Expected:
- `status` 输出为空

---

### Task B7: 输出目录可重复运行（默认拒绝污染，显式 `--overwrite` 才清理）

**Files:**
- Modify: `scripts/adapt_selfcap_release_to_freetime.py`
- Test: `scripts/tests/test_selfcap_parsers.py`

**Step 1: 写一个失败用例：输出目录非空时应失败**

在 `scripts/tests/test_selfcap_parsers.py` 追加一个新测试（不运行完整 adapter）：
- 新增 helper：`adapter.ensure_empty_or_overwrite(out_root, overwrite=False)`（先假设存在）
- 构造一个临时目录，写入一个哨兵文件 `out_dir/DO_NOT_TOUCH`
- 调用 `ensure_empty_or_overwrite(..., overwrite=False)` 期望抛 `RuntimeError` 或 `ValueError`

**Step 2: 运行测试确认失败**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_selfcap_parsers.py
```

Expected:
- FAIL（提示缺少函数或未抛错）

**Step 3: 最小实现 `ensure_empty_or_overwrite`**

在 `scripts/adapt_selfcap_release_to_freetime.py` 增加函数：
```python
def ensure_empty_or_overwrite(out_root: Path, overwrite: bool) -> None:
    # If out_root exists and has any entries, refuse unless overwrite=True.
    # If overwrite=True, delete known subdirs: images/, sparse/, triangulation/.
```

并在 `main()` 开始创建目录之前调用：
- `--overwrite` 缺省为 False
- 仅清理 `images/`, `sparse/`, `triangulation/`，不删除 `out_root` 本身

**Step 4: 补一个通过用例：`--overwrite` 应清理并继续**

在同一测试文件追加：
- 创建 `out_dir/images/old.jpg`、`out_dir/triangulation/old.npy`
- 调用 `ensure_empty_or_overwrite(..., overwrite=True)`
- 断言这些旧路径被删除（`not exists`）

**Step 5: 复跑测试确认通过**

Run: 同 Step 2  
Expected: `OK`

**Step 6: 提交**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
git add scripts/adapt_selfcap_release_to_freetime.py scripts/tests/test_selfcap_parsers.py
git commit -m "feat(selfcap): add overwrite-safe output dir handling"
```

---

### Task B8: 增加 `--no_images`（无视频也能导出 tri+sparse，用于快速链路验证）

**Files:**
- Modify: `scripts/adapt_selfcap_release_to_freetime.py`
- Test: `scripts/tests/test_selfcap_parsers.py` 或新建 `scripts/tests/test_selfcap_cli_no_images.py`

**Step 1: 写失败用例：最小 tar.gz + `--no_images` 可跑通**

新增一个 CLI 集成测试（建议新文件 `scripts/tests/test_selfcap_cli_no_images.py`）：
- 用 `tarfile` 现场打一个极小 `bar-release.tar.gz`，包含：
  - `bar-release/optimized/intri.yml`（只要 `K_02`，可选 `dist_02`）
  - `bar-release/optimized/extri.yml`（`Rot_02`、`T_02`）
  - `bar-release/pcds/000000.ply`、`bar-release/pcds/000001.ply`（用二进制 PLY 写 3 个点即可）
- 不放 `videos/`（故意缺失）
- `subprocess.run` 调用：
  - `--no_images --image_width 640 --image_height 480`
  - `--camera_ids 02 --frame_start 0 --num_frames 2`
- 断言输出存在：
  - `output_dir/triangulation/points3d_frame000000.npy`、`...000001.npy`
  - `output_dir/sparse/0/cameras.bin`（至少 1 个相机）

**Step 2: 运行测试确认失败**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/tests/test_selfcap_cli_no_images.py
```

Expected:
- FAIL（当前脚本会尝试读取 `videos/<cam>.mp4`）

**Step 3: 最小实现 `--no_images`**

在 `argparse` 增加：
- `--no_images`（action store_true）
- `--image_width`、`--image_height`（默认 0）

逻辑：
- 若 `--no_images`：
  - 跳过 “从视频抽帧” 环节
  - 要求 `--image_width > 0 && --image_height > 0`，否则报错
  - 仍创建 `images/<cam>/` 目录（可为空）
- 若非 `--no_images`：
  - 维持现状：OpenCV 解码并写帧，同时得到 `image_width/height`

**Step 4: 复跑测试确认通过**

Expected:
- `PASS/OK`

**Step 5: 提交**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
git add scripts/adapt_selfcap_release_to_freetime.py scripts/tests/test_selfcap_cli_no_images.py
git commit -m "feat(selfcap): add --no_images mode for tri+sparse export"
```

---

### Task B9: 支持畸变模型（`dist_*` 非零时写 `OPENCV` 相机）

**Files:**
- Modify: `scripts/adapt_selfcap_release_to_freetime.py`
- Modify: `scripts/tests/test_selfcap_parsers.py`

**Step 1: 写失败用例：dist 非零时 camera.model=OPENCV**

扩展 `scripts/tests/test_selfcap_parsers.py::test_write_colmap_sparse0`：
- 在 intrinsics dict 中加入 `dist_02`（至少 4 个值，k1 非 0）
- 调用 `write_colmap_sparse0(...)`
- 用 `read_write_model.read_model()` 读取 `cameras.bin`
- 断言：
  - `camera.model == "OPENCV"`
  - `len(camera.params) == 8`
  - `fx/fy/cx/cy` 会按 `image_downscale` 缩放（例如 downscale=2 则 fx/2）

**Step 2: 运行测试确认失败**

Expected:
- FAIL（当前一律 PINHOLE）

**Step 3: 最小实现**

在 `write_colmap_sparse0`：
- 读取 `dist_key = f"dist_{cam}"`
- 若存在且 `max(abs(dist[:4])) > 1e-12`：
  - `model="OPENCV"`
  - `params=[fx,fy,cx,cy,k1,k2,p1,p2]`
- 否则保持 `PINHOLE`

**Step 4: 复跑测试确认通过**

Expected:
- `OK`

**Step 5: 提交**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
git add scripts/adapt_selfcap_release_to_freetime.py scripts/tests/test_selfcap_parsers.py
git commit -m "feat(selfcap): write OPENCV cameras when distortion is present"
```

---

### Task B10 (Optional): GPU1 10 steps sanity（确认新 flag 不破坏现有 Gate-1 路线）

**Files:**
- None (outputs only)

**Step 1: 重新产数（覆盖输出目录）**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
PY=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python
$PY scripts/adapt_selfcap_release_to_freetime.py \
  --tar_gz data/selfcap/bar-release.tar.gz \
  --output_dir data/selfcap_bar_8cam60f \
  --camera_ids 02,03,04,05,06,07,08,09 \
  --frame_start 0 \
  --num_frames 60 \
  --image_downscale 2 \
  --seed 0 \
  --overwrite
```

Expected:
- 完成且输出目录结构不变

**Step 2: 10 steps 快速训练**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260224-selfcap-hardening
source /root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/activate
CUDA_VISIBLE_DEVICES=1 python third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py default_keyframe_small \
  --data-dir data/selfcap_bar_8cam60f \
  --init-npz-path outputs/gate1_selfcap_bar_8cam60f/keyframes_60frames_step5.npz \
  --result-dir outputs/gate1_selfcap_bar_8cam60f_hardened_sanity \
  --start-frame 0 --end-frame 60 \
  --max-steps 10 --eval-steps 10 --save-steps 10 \
  --render-traj-path fixed \
  --global-scale 6
```

Expected:
- 产物出现：`outputs/gate1_selfcap_bar_8cam60f_hardened_sanity/stats/val_step0010.json`（或 step0009）

---

### Task B11: 提交 PR 备注（给 A 的集成分支合流用）

**Files:**
- None

**Step 1: 汇总给 A 的合流要点（写到 `notes/` 或直接发消息）**

内容包含：
- 新增/变更的 flags：`--overwrite`、`--no_images`、`--image_width/--image_height`
- 畸变支持：`OPENCV` 触发条件
- 新增测试文件列表

