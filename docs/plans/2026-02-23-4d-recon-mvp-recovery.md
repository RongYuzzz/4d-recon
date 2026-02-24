# 4D Recon MVP Recovery Implementation Plan

> 状态：已完成（存档）。不要再按本文执行；当前入口以 `README.md` / `notes/demo-runbook.md` 为准。

**Goal:** 在 `2026-02-25` 汇报前，把当前“环境已就绪但无实验证据”的状态推进到“可演示、可复现、可答辩”的最小交付。

**Architecture:** 先走最短关键路径：`数据就位 -> T0 四项检查最小闭环 -> Go/No-Go 判定 -> 证据打包`。由于当前日期是 `2026-02-23`，已晚于原计划 `2026-02-20` 闸门，严格执行范围冻结：不扩功能，只产出证据。若 T0 失败，立即切换到 Deformable-GS 最小闭环，保住演示与表格。

**Tech Stack:** Bash, Python, PyTorch, COLMAP, FreeTimeGsVanilla

---

### Task 1: 数据阻塞解除（今天立即完成）

**Files:**
- Modify: `notes/decision-log.md`
- Create: `notes/data-manifest.md`
- Use: `scripts/export_triangulation_from_colmap_sparse.py`

**Step 1: 准备场景目录（单场景）**

Run: `mkdir -p data/scene01/{colmap,triangulation}`
Expected: `data/scene01/colmap` 与 `data/scene01/triangulation` 存在。

**Step 2: 放置 COLMAP 数据并验证结构**

Run: `find data/scene01/colmap -maxdepth 3 -type f | sort`
Expected: 至少包含 `images/` 与 `sparse/0/{cameras.bin,images.bin,points3D.bin}`。

**Step 3: 若无三角化产物，则由 COLMAP 导出**

Run: `python scripts/export_triangulation_from_colmap_sparse.py --colmap_data_dir data/scene01/colmap --out_dir data/scene01/triangulation --frame_start 0 --frame_end -1 --max_points 200000 --seed 0`
Expected: 产出 `points3d_frame*.npy`、`colors_frame*.npy`、`frame_manifest.csv`。

**Step 4: 写数据清单**

Run: `python - <<'PY'\nfrom pathlib import Path\ntri=Path('data/scene01/triangulation')\npts=sorted(tri.glob('points3d_frame*.npy'))\ncols=sorted(tri.glob('colors_frame*.npy'))\nprint('points files:',len(pts))\nprint('colors files:',len(cols))\nprint('manifest exists:',(tri/'frame_manifest.csv').exists())\nPY`
Expected: `points files == colors files > 0`。

**Step 5: 记录到日志**

在 `notes/data-manifest.md` 写入：场景名、帧数、来源路径、采样设置；在 `notes/decision-log.md` 新增 “Data Unblocked” 条目。

---

### Task 2: T0 最小闭环（baseline vs zero-velocity）

**Files:**
- Use: `scripts/run_t0_zero_velocity.sh`
- Modify: `scripts/t0_grad_check.md`
- Modify: `notes/decision-log.md`

**Step 1: 运行 T0 对比实验**

Run: `bash scripts/run_t0_zero_velocity.sh data/scene01/triangulation data/scene01/colmap outputs/t0_zero_velocity 0 -1 5 0 default_keyframe_small`
Expected: `outputs/t0_zero_velocity/baseline` 与 `outputs/t0_zero_velocity/zero_velocity` 均有训练产物。

**Step 2: 检查梯度 CSV 是否生成**

Run: `find outputs/t0_zero_velocity -name 't0_grad.csv' | sort`
Expected: 至少 2 个文件（baseline + zero_velocity）。

**Step 3: 计算梯度健康度（finite + 非全 0）**

Run: `python - <<'PY'\nimport csv, math, pathlib\nfor p in [pathlib.Path('outputs/t0_zero_velocity/baseline/t0_grad.csv'), pathlib.Path('outputs/t0_zero_velocity/zero_velocity/t0_grad.csv')]:\n    if not p.exists():\n        print(p, 'MISSING'); continue\n    rows=list(csv.DictReader(p.open()))\n    gv=[float(r.get('grad_v_norm',0) or 0) for r in rows]\n    gd=[float(r.get('grad_duration_norm',0) or 0) for r in rows]\n    finite=all(math.isfinite(x) for x in gv+gd)\n    nonzero_v=sum(1 for x in gv if abs(x)>0)\n    nonzero_d=sum(1 for x in gd if abs(x)>0)\n    print(p, 'rows=',len(rows), 'finite=',finite, 'nonzero_v=',nonzero_v, 'nonzero_d=',nonzero_d)\nPY`
Expected: `finite=True`，且 `nonzero_v/nonzero_d` 非 0。

**Step 4: 填写结论**

更新 `scripts/t0_grad_check.md`：把 `PENDING` 改成 `PASS/FAIL` 并附数值摘要；更新 `notes/decision-log.md`：写 T0 四项中已验证项与未验证项。

---

### Task 3: Go/No-Go 决策（今天内完成）

**Files:**
- Modify: `notes/decision-log.md`
- Create: `notes/t0-gate-decision.md`

**Step 1: 套用硬闸门规则**

判定规则：
- Go：T0 四项检查均可给出 PASS 证据。
- No-Go：任一关键项 FAIL 或无法在今晚补齐证据。

**Step 2: 生成一页决策文档**

`notes/t0-gate-decision.md` 必须包含：
- 判定时间（绝对时间戳）
- 证据文件路径
- 风险清单
- 明日执行路线（Go 路线或 No-Go 路线）

**Step 3: 同步路线**

- Go 路线：继续 FreeTimeGS，进入证据打包。
- No-Go 路线：立即切 Deformable-GS 最小闭环，不再修线性运动基底。

---

### Task 4: 证据包最小交付（`2026-02-24`）

**Files:**
- Create: `outputs/report_pack/metrics.csv`
- Create: `outputs/report_pack/ablation_notes.md`
- Create: `outputs/report_pack/failure_cases.md`
- Create: `scripts/run_mvp_repro.sh`
- Modify: `README.md`

**Step 1: 产出 1 组可播放演示**

Run: `find outputs -type f | rg -n '\\.(mp4|gif|webm)$'`
Expected: 至少 1 个可播放视频（本地可打开）。

**Step 2: 产出 1 张最小指标表**

`outputs/report_pack/metrics.csv` 列：`scene,method,psnr,ssim,lpips,notes`。

**Step 3: 产出 1 组消融说明**

`outputs/report_pack/ablation_notes.md` 至少包含：`baseline vs zero_velocity`，若有 weak/strong 再补充。

**Step 4: 产出失败分析**

`outputs/report_pack/failure_cases.md` 至少写 3 条机制级失败（例如时间尺度错配、梯度断裂、遮挡错配）。

**Step 5: 一键复现脚本**

`bash scripts/run_mvp_repro.sh` 至少能串起：数据检查 -> T0 运行 -> 结果汇总。

---

### Task 5: 汇报日保障（`2026-02-25` 当天）

**Files:**
- Create: `notes/demo-runbook.md`
- Create: `notes/qna.md`

**Step 1: 演示脚本化**

`notes/demo-runbook.md` 写清楚：启动命令、展示顺序、每段时长、异常兜底动作。

**Step 2: 离线备份**

Run: `tar -czf outputs/report_pack_2026-02-25.tar.gz outputs/report_pack outputs/t0_zero_velocity notes`
Expected: 生成离线包，断网也可展示。

**Step 3: 口径统一**

`notes/qna.md` 固定三件事：Training-free 边界、Go/No-Go 决策依据、下一阶段计划。

---

## 快速执行顺序（你现在就按这个跑）

1. 完成 Task 1（数据就位）
2. 完成 Task 2（跑出 baseline/zero_velocity + 梯度结论）
3. 完成 Task 3（今晚给出 Go/No-Go）
4. `2026-02-24` 完成 Task 4（证据包）
5. `2026-02-25` 执行 Task 5（演示与备份）
