# THUman4 Oracle Weak Decision (2026-03-06)

## Scope

- 原计划优先在 `SelfCap` 上跑 `oracle backgroundness weak-fusion`。
- 实际执行前发现 `data/selfcap_bar_8cam60f` 没有 `masks/`，无法满足 `export_oracle_background_pseudo_masks_npz.py` 与 `mask_source=dataset` 的前提。
- 因此切换到本机已具备 `masks/` 与 `triangulation/` 的 `data/thuman4_subject00_8cam60f` 做验证。
- 所以这份文档**只能支撑 THUman4 上的判断**，**不能直接回答 SelfCap 上是否成立**。
- 另外，本次 THUman4 初始化/triangulation 明显偏弱；因此本文件更适合表述为“**弱初始化条件下的现象记录**”，而不是泛化结论。

## Executive Summary

### What current evidence does support

- **可支撑**：在 `THUman4 / weak init / seed42 / 600 steps` 这个狭窄条件下，`oracle backgroundness weak-fusion` 是正例。
- **可支撑**：在 `THUman4 / 4 seeds / smoke200` 下，这条线按当前 gate 应判定为 `stop`。

### What current evidence does not support

- **不能支撑**：`oracle weak` 一般性地属于 **late-emerging positive**。当前这最多只是一个**待验证假说**，不是结论。
- **不能支撑**：基于当前证据去修改现有 smoke gate。
- **不能支撑**：把 THUman4 上的结果外推到 SelfCap。

### Decision recommendation

- 如果现在必须做项目决策，推荐：**先做一个最小补充实验，再决定**。
- 这个“最小补充实验”应严格限定为：**补 2 个非 42 seed 的 600-step 复核**，不再继续追加 `200-step` 权重扫。
- 在补齐这 2 个 `600-step` seed 之前，文档中关于“late-emerging positive”的表述都应视为**假说/线索**，不能写成结论。

## Single-seed 600 result

### Setup

- Baseline: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s42`
- Oracle weak: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s42`
- Eval: `stats_masked/test_step0599.json`, `mask_source=dataset`, `bbox_margin_px=32`, `boundary_band_px=2`, `lpips_backend=auto`
- Single-seed pass gate:
  - `Δpsnr_fg_area >= +0.2`
  - `Δlpips_fg_comp <= -0.003`
  - `Δtlpips <= +0.01`
  - boundary-band 至少一项改善：`Δpsnr_bd_area >= +0.2` 或 `Δlpips_bd_comp <= -0.001`
- Core artifacts:
  - `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s42/stats_masked/test_step0599.json`
  - `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s42/stats_masked/test_step0599.json`

### Exact commands used

```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f

SEED=42 MAX_STEPS=600 DATA_DIR="$DATA" VENV_PYTHON="$VENV" \
  RESULT_DIR="$WT/outputs/thuman4_oracle_weak_mve/baseline_s42" \
  bash "$WT/scripts/run_train_planb_init_selfcap.sh"

SEED=42 MAX_STEPS=600 DATA_DIR="$DATA" VENV_PYTHON="$VENV" \
  RESULT_DIR="$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s42" \
  ORACLE_DIR="$WT/outputs/cue_mining/thuman4_oracle_bg_s42" \
  bash "$WT/scripts/run_train_ours_weak_oracle_bg_selfcap.sh"

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$WT/outputs/thuman4_oracle_weak_mve/baseline_s42" \
  --stage test --step 599 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2

"$VENV" "$WT/scripts/eval_masked_metrics.py" \
  --data_dir "$DATA" \
  --result_dir "$WT/outputs/thuman4_oracle_weak_mve/oracle_weak_s42" \
  --stage test --step 599 --mask_source dataset \
  --bbox_margin_px 32 --lpips_backend auto --boundary_band_px 2
```

### Metrics delta (oracle weak - baseline)

- `Δpsnr = +0.0691`
- `Δssim = +0.0192`
- `Δlpips = +0.00792` (full-image worse)
- `Δtlpips = +0.000120` (guardrail pass)
- `Δpsnr_fg_area = +1.6766`
- `Δlpips_fg_comp = -0.004373`
- `Δpsnr_bd_area = +1.3603`
- `Δlpips_bd_comp = -0.000834`

### Single-seed decision

- 按上述单 seed gate：**PASS**。
- 其中 boundary 子条件是靠 `Δpsnr_bd_area=+1.3603` 过线；`Δlpips_bd_comp=-0.000834` 本身没有越过 `-0.001` 阈值。
- 因此，当前证据**足以支撑**下面这句狭窄陈述：
  - **在 `THUman4 / weak init / seed42 / 600 steps` 下，`oracle backgroundness weak-fusion` 是正例。**
- 但这还**不足以推出**“该方法在 THUman4 上一般性成立”或“它是稳定的晚期收益机制”。

## Multi-seed smoke200 result

### Setup

- Driver: `scripts/run_oracle_weak_smoke200_multiseed.sh`
- Output root: `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed`
- Seeds: `41,42,43,44`
- Steps: `200` (`test_step0199.json`)
- Per-seed pass gate:
  - `Δpsnr_fg_area >= +0.2`
  - `Δlpips_fg_comp <= -0.003`
  - `Δtlpips <= +0.01`
  - boundary-band 至少一项改善：`Δpsnr_bd_area >= +0.2` 或 `Δlpips_bd_comp <= -0.001`
- Runner-level decision:
  - `pass_count >= 3/4` => `continue`
  - 否则 => `stop`
- Core artifacts:
  - `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/baseline/stats_masked/test_step0199.json`
  - `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/oracle_weak/stats_masked/test_step0199.json`
  - `outputs/thuman4_oracle_weak_smoke200_multiseed/seed42/.../test_step0199.json`
  - `outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/.../test_step0199.json`
  - `outputs/thuman4_oracle_weak_smoke200_multiseed/seed44/.../test_step0199.json`

### Exact command used

```bash
ROOT=/root/autodl-tmp/projects/4d-recon
WT=$ROOT/.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak
VENV=$ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python
DATA=$ROOT/data/thuman4_subject00_8cam60f
OUT=$WT/outputs/thuman4_oracle_weak_smoke200_multiseed

OMP_NUM_THREADS=1 VENV_PYTHON="$VENV" DATA_DIR="$DATA" \
  MAX_STEPS=200 PSEUDO_MASK_WEIGHT=0.8 PSEUDO_MASK_END_STEP=200 \
  LPIPS_BACKEND=auto BOUNDARY_BAND_PX=2 SEEDS=41,42,43,44 \
  bash "$WT/scripts/run_oracle_weak_smoke200_multiseed.sh" "$OUT"
```

### Runner summary

- `seed=41 pass=False d_psnr_fg_area=+0.0888 d_lpips_fg_comp=-0.000047 d_tlpips=-0.000037 d_psnr_bd_area=+0.0575 d_lpips_bd_comp=-0.000089`
- `seed=42 pass=False d_psnr_fg_area=+0.0958 d_lpips_fg_comp=+0.000568 d_tlpips=+0.000046 d_psnr_bd_area=+0.0208 d_lpips_bd_comp=+0.000237`
- `seed=43 pass=False d_psnr_fg_area=+0.0947 d_lpips_fg_comp=+0.000584 d_tlpips=+0.000153 d_psnr_bd_area=+0.0546 d_lpips_bd_comp=-0.000007`
- `seed=44 pass=False d_psnr_fg_area=+0.0797 d_lpips_fg_comp=+0.000264 d_tlpips=-0.000066 d_psnr_bd_area=+0.0312 d_lpips_bd_comp=+0.000035`
- Mean delta across 4 seeds:
  - `mean Δpsnr_fg_area = +0.08975`
  - `mean Δlpips_fg_comp = +0.000342`
  - `mean Δpsnr_bd_area = +0.04100`
  - `mean Δlpips_bd_comp = +0.0000439`
  - `mean Δtlpips = +0.0000239`
- Final summary: `pass_count=0/4`, `decision=stop`

### Smoke200 decision

- 按 smoke200 gate：**STOP**。
- 因此，当前证据**足以支撑**下面这句结论：
  - **在 THUman4 上，这条线不是 smoke-robust early effect；`200-step` 阶段没有稳定越过 ROI gate。**
- 这一步的结论强度高于“late-emerging”判断，因为它基于 4 个 seed 的对等 smoke 对比，而不是单点长跑。

## Evidence gaps and strongest objections

### Gap 1: Non-equivalent sample sizes

- 当前最致命的缺口是：`600-step` 只有 `seed42`，但 `smoke200` 有 `4 seeds`。
- `seed42` 在 `200-step` 时仅有 `Δpsnr_fg_area=+0.0958`，到 `600-step` 却跳到 `+1.6766`。
- 如果没有补 `seed41/43/44` 的 `600-step`，就不能证明这是“普遍存在的后期跃升”；它完全可能只是 `seed42` 的偶然离群值。

### Gap 2: Weak baseline / rescue-the-brick risk

- 当前 THUman4 初始化明显偏弱：`combine_frames_fast_keyframes.py` 只处理到 `1/12` keyframes，`Plan-B velocity_stats.json` 的 `match_ratio_over_eligible` 也接近 `0.0000`。
- 因此 `Δpsnr_fg_area=+1.6766` 这类大幅度相对收益，更像是在回答“oracle weak 能否在弱初始化里救砖”，而不是“它在正常初始化下是否依然有普适增益”。
- 这不否定现象本身，但会显著限制它的泛化解释。

### Gap 3: Dataset switch changed the original question

- 原问题本来想在 `SelfCap` 上验证，但因为缺少 `masks/`，实际改在 `THUman4` 上完成。
- 所以 THUman4 的结果只能回答“THUman4 上发生了什么”，不能自动变成“SelfCap 上也该如此”。

## Interpretation after review tightening

- 当前数据支持的是 **mixed-evidence split**：
  - `4-seed smoke200`：没有早期稳健收益；
  - `3-seed 600-step replication`：`2/3` 过线，`seed41` 为 mixed-evidence seed (gate-fail)；
  - `199 / 399 / 599` triad：中段已出现明显 ROI / boundary 分离，但 LPIPS 转化呈 seed-dependent 分叉。
- 因此，当前最稳妥表述不是“已证实的 late-emerging positive”，而是：
  - **存在 late rescue / LPIPS conversion split 线索，但尚不足以升级为可复现 late-emerging mechanism。**
- route-level 决策保持：
  - **mixed evidence -> stop**；
  - 不据此修改现有 smoke gate。

## Decision recommendation

### Historical note (superseded)

- 预复核阶段曾给出“如果必须立刻决定，推荐 `B=补最小实验后再决定`”与“唯一值得继续投入的是补 2 个非42 seed 的 `600-step` 复核”。
- 该建议在 2026-03-06 已被完整执行（`seed41/43` 的 `600-step` 复核 + `step399` 中间截面包），现仅保留为历史上下文。

### Current active decision state

- **This pre-follow-up recommendation is now superseded by the completed 3-seed replication check.**
- **Current route-level status remains: mixed evidence -> stop.**
- 当前 route-level 的唯一有效动作仍是：维持 `stop`，不重开 line-level 投入。

## Additional operational notes

- 运行期间反复出现 `libgomp: Invalid value for environment variable OMP_NUM_THREADS` 告警；本次通过显式设置 `OMP_NUM_THREADS=1` 跑通，不影响结果判读。
- 当前最适合带去讨论的核心结论是：
  - **3-seed 600-step replication 仍是 mixed evidence（`2/3` pass，其中 `seed41` 为 mixed-evidence seed (gate-fail)）；route-level 决策继续 `stop`。**

## Follow-up checkpoint (3-seed 600-step replication, 2026-03-06)

### Execution scope locked

- 本轮只执行计划规定的两组新 seed：`41`、`43`（备用 `44` 未启用）。
- 数据、脚本、评估参数保持与 `seed42` 一致：`mask_source=dataset`、`bbox_margin_px=32`、`boundary_band_px=2`、`lpips_backend=auto`。
- 本轮只更新根仓库主文档：`notes/2026-03-06-thuman4-oracle-weak-decision.md`；不更新 `$WT/notes/...` 旧副本。

### 600-step masked delta summary (oracle weak - baseline)

- `seed=42 pass=True d_psnr_fg_area=+1.676596 d_lpips_fg_comp=-0.004373 d_psnr_bd_area=+1.360299 d_lpips_bd_comp=-0.000834 d_tlpips=+0.000120`
- `seed=41 pass=False d_psnr_fg_area=+1.580751 d_lpips_fg_comp=-0.000849 d_psnr_bd_area=+0.609282 d_lpips_bd_comp=-0.000472 d_tlpips=+0.000023`
- `seed=43 pass=True d_psnr_fg_area=+1.678506 d_lpips_fg_comp=-0.004560 d_psnr_bd_area=+0.705789 d_lpips_bd_comp=-0.000550 d_tlpips=-0.000192`

### Replication count and interpretation

- 复核规则：`replicated = number of non-42 seeds that also pass the same 600-step gate`。
- 当前结果：`replicated = 1/2`（`seed43` 过线，`seed41` 未过线）。
- 结论约束：`replicated < 2/2`，因此**不得**写成“late-emerging 已证实”；目前仍是**弱证据/线索**。

### Checkpoint decision (this round)

- 最终决策：**stop**（停止这条 oracle-weak 线的 line-level 投入）。
- 原因 1（为何 stop）：`1/2` 属于 mixed evidence，未达到可复现门槛。
- 原因 2（为何不改 smoke gate）：现有 gate 针对早期稳健性；当前证据仍不足以支持规则级变更。
- 原因 3（为何不继续做 200-step 权重扫）：核心不确定性是 `600-step` 可复现性，而不是 `200-step` 阈值微调。
- 原因 4（为何只维护根仓库主 note）：避免根仓库与 worktree 双文档分叉，后续讨论以单一事实底稿为准。

### If supervisor explicitly asks for one tie-break

- 仅在被明确要求时，才允许补 `seed44` 作为单次 tie-break；否则按本轮结论维持 `stop`。

## Detailed analysis appendix

### Document purpose

- 这部分用于把当前 `oracle backgroundness weak-fusion` 线的**实现链路、关键数据、判定逻辑、问题清单和最终解释**收拢到同一份文档中。
- 所有结论仅基于仓库内现有工件：训练输出、`stats_masked/*.json`、执行计划、以及当前根仓库主 note。
- 这部分是**详细分析**，不改变前文已经写明的 checkpoint 决策：当前结论仍然是 **stop**。

### Current status in one paragraph

- 当前链路已经跑通：ROI / boundary evaluator、oracle background pseudo mask 导出、oracle weak runner、THUman4 上的 `600-step` baseline-vs-oracle 对照、以及 `4-seed smoke200` 复核都已经完成。
- 结果表现为：`smoke200` 没有任何一个 seed 稳定过线，但 `600-step` 的 `seed42` 与 `seed43` 都显示出明显 ROI 改善；`seed41` 虽然 PSNR 向指标改善很大，但因为 `lpips_fg_comp` 改善不够，仍按完整 gate 判定为失败。
- 因此，这条线不是“彻底无效”，但也还不够强到能被认定为“可复现 late-emerging mechanism”；按照预先写明的规则，当前应收口为 **mixed evidence -> stop**。

### What was actually implemented and verified

#### 1. Evaluator metrics are no longer only fill-black

当前评估输出已经同时包含全图指标、历史 fill-black 指标、以及更贴近 silhouette 质量的 ROI / boundary 指标。关键输出字段如下：

```python
out = {
    "stage": stage,
    "step": step,
    "mask_source": args.mask_source,
    "bbox_margin_px": margin,
    "mask_thr": float(args.mask_thr),
    "boundary_band_px": int(args.boundary_band_px),
    "lpips_backend": args.lpips_backend,
    "psnr": base_stats.get("psnr", ""),
    "ssim": base_stats.get("ssim", ""),
    "lpips": base_stats.get("lpips", ""),
    "tlpips": base_stats.get("tlpips", ""),
    "psnr_fg": float(np.mean(psnr_list)) if psnr_list else float("nan"),
    "lpips_fg": float(np.mean(lpips_list)) if lpips_list else float("nan"),
    "psnr_fg_area": float(np.nanmean(psnr_area_list)) if psnr_area_list else float("nan"),
    "lpips_fg_comp": float(np.mean(lpips_comp_list)) if lpips_comp_list else float("nan"),
    "psnr_bd_area": float(np.nanmean(psnr_bd_area_list)) if psnr_bd_area_list else float("nan"),
    "lpips_bd_comp": float(np.mean(lpips_bd_comp_list)) if lpips_bd_comp_list else float("nan"),
}
```

这意味着当前结论不是建立在旧的 `psnr_fg/lpips_fg` fill-black 口径上，而是建立在更可信的：
- `psnr_fg_area`
- `lpips_fg_comp`
- `psnr_bd_area`
- `lpips_bd_comp`
- `tlpips`

#### 2. Oracle weak runner is a thin wrapper, not a hidden new algorithm

当前 oracle weak 线的关键脚本逻辑非常直接：如果不存在 `pseudo_masks.npz`，先从 dataset `masks/` 生成 oracle backgroundness pseudo mask；然后把该 NPZ 交给现有 weak runner。

```bash
if [ ! -f "$PSEUDO_MASK_NPZ" ]; then
  "$VENV_PYTHON" "$REPO_ROOT/scripts/export_oracle_background_pseudo_masks_npz.py" \
    --data_dir "$DATA_DIR" \
    --out_npz "$PSEUDO_MASK_NPZ" \
    --frame_start "$START_FRAME" \
    --num_frames "$((END_FRAME - START_FRAME))" \
    --mask_downscale "$MASK_DOWNSCALE" \
    --mask_thr "$MASK_THR" \
    --overwrite
fi

PSEUDO_MASK_NPZ="$PSEUDO_MASK_NPZ" \
PSEUDO_MASK_WEIGHT="$PSEUDO_MASK_WEIGHT" \
PSEUDO_MASK_END_STEP="$PSEUDO_MASK_END_STEP" \
  bash "$REPO_ROOT/scripts/run_train_ours_weak_selfcap.sh" "$RESULT_DIR"
```

这点很重要，因为它说明本轮实验主要是在验证：
- **当 oracle-quality 的背景降权先验可用时，现有 weak-fusion 管线是否能产生可审计增益**；
- 而不是同时引入额外复杂模型改动，导致因果难以分离。

#### 3. Current gate is explicit and auditable

本轮 `600-step` 复核使用的是与前文一致的分析 gate：

```python
passed = (
    d_psnr_fg_area >= 0.2 and
    d_lpips_fg_comp <= -0.003 and
    d_tlpips <= 0.01 and
    (d_psnr_bd_area >= 0.2 or d_lpips_bd_comp <= -0.001)
)
```

也就是说，一个 seed 要通过，不仅要有 ROI PSNR 改善，还要同时满足：
- ROI 感知指标 `lpips_fg_comp` 明显改善；
- 时序 guardrail `tlpips` 不恶化；
- boundary-band 至少有一项达标。

因此，本轮 `seed41` 的失败不是“没有提升”，而是“**没有通过完整 gate**”。

### Experiment matrix

| experiment | dataset | seeds | steps | purpose | outcome |
| --- | --- | --- | --- | --- | --- |
| single-seed 600 | THUman4 | 42 | 600 | 首次验证 oracle weak 是否可能出现后期正例 | pass |
| smoke200 multiseed | THUman4 | 41,42,43,44 | 200 | 验证早期是否为稳健效应 | `pass_count=0/4`, stop |
| follow-up 600 | THUman4 | 41 | 600 | 复核 `seed42` 是否可复现 | fail |
| follow-up 600 | THUman4 | 43 | 600 | 复核 `seed42` 是否可复现 | pass |
| replication checkpoint | THUman4 | 41,42,43 | 600 | 汇总 3-seed 长跑结果并做路线决策 | `replicated=1/2`, stop |

### Raw 600-step data (auditable)

#### A. Raw masked metrics at `test_step0599`

| seed | variant | psnr | ssim | lpips | tlpips | psnr_fg_area | lpips_fg_comp | psnr_bd_area | lpips_bd_comp |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 41 | baseline | 17.194172 | 0.577444 | 0.696022 | 0.001755 | 13.521910 | 0.042188 | 13.909433 | 0.016657 |
| 41 | oracle weak | 16.670124 | 0.598916 | 0.720039 | 0.001777 | 15.102661 | 0.041339 | 14.518715 | 0.016185 |
| 42 | baseline | 17.546217 | 0.587731 | 0.686752 | 0.001261 | 12.211166 | 0.047154 | 12.720415 | 0.017134 |
| 42 | oracle weak | 17.615337 | 0.606892 | 0.694673 | 0.001381 | 13.887763 | 0.042781 | 14.080714 | 0.016300 |
| 43 | baseline | 17.601793 | 0.592871 | 0.691203 | 0.000976 | 13.794996 | 0.047795 | 13.963241 | 0.016251 |
| 43 | oracle weak | 16.540054 | 0.627739 | 0.702332 | 0.000784 | 15.473502 | 0.043236 | 14.669030 | 0.015701 |

#### B. Delta table and gate result

| seed | d_psnr | d_ssim | d_lpips | d_tlpips | d_psnr_fg_area | d_lpips_fg_comp | d_psnr_bd_area | d_lpips_bd_comp | pass | main reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 41 | -0.524048 | +0.021472 | +0.024016 | +0.000023 | +1.580751 | -0.000849 | +0.609282 | -0.000472 | no | `lpips_fg_comp` 未达到 `<= -0.003` |
| 42 | +0.069120 | +0.019161 | +0.007922 | +0.000120 | +1.676596 | -0.004373 | +1.360299 | -0.000834 | yes | ROI 两项 + boundary PSNR 达标 |
| 43 | -1.061739 | +0.034868 | +0.011129 | -0.000192 | +1.678506 | -0.004560 | +0.705789 | -0.000550 | yes | ROI 两项 + boundary PSNR 达标 |

#### C. 200-step vs 600-step comparison for the three audited seeds

| seed | smoke200 d_psnr_fg_area | smoke200 d_lpips_fg_comp | smoke200 d_psnr_bd_area | smoke200 d_lpips_bd_comp | smoke200 d_tlpips | 600 d_psnr_fg_area | 600 d_lpips_fg_comp | 600 pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 41 | +0.088835 | -0.000047 | +0.057479 | -0.000089 | -0.000037 | +1.580751 | -0.000849 | no |
| 42 | +0.095795 | +0.000568 | +0.020761 | +0.000237 | +0.000046 | +1.676596 | -0.004373 | yes |
| 43 | +0.094709 | +0.000584 | +0.054605 | -0.000007 | +0.000153 | +1.678506 | -0.004560 | yes |

这张表展示了当前证据最关键的结构：
- 早期 `200-step` 时，三个 seed 都没有显著越过 ROI gate；
- 到 `600-step` 时，三个 seed 都出现了**很大的 ROI PSNR 增益**；
- 但只有 `42` 和 `43` 的 `lpips_fg_comp` 也同步改善到达标区间，`41` 没有。

### What the data actually says

#### 1. This line is not a clean negative

如果只看 `psnr_fg_area` 和 `psnr_bd_area`，三条 `600-step` 线都表现出强烈正向变化；尤其 `seed41` 的 `d_psnr_fg_area=+1.580751` 并不小。

因此，把当前结果简单概括成“oracle weak 无效”是不准确的。更精确的说法应该是：
- **该方向存在后期 ROI 改善迹象；**
- **但这种改善并没有在当前完整 gate 下稳定复现。**

#### 2. Why `seed41` failed matters more than the raw fail label

`seed41` 的失败机制并不是：
- ROI 没提升；
- 或 boundary 没提升；
- 或 tLPIPS 爆掉。

它真正失败的原因是：
- `d_lpips_fg_comp=-0.000849`，改善方向正确，但**改善幅度不足以越过 `-0.003` 阈值**。

这意味着 `seed41` 更像是：
- **结构/像素向指标变好；**
- **但感知向 ROI 改善不够强。**

这也是为什么当前状态应被描述为 **mixed evidence**，而不是单纯的“1 positive + 1 irrelevant negative”。

#### 3. Why we still stop despite seeing two 600-step passes

当前 stop 不是因为“结果不好看”，而是因为我们在 follow-up 计划里预先写明了更严格的 replication rule：
- follow-up 的问题不是“总共有几个 seed pass”，而是“**新增的两个非 42 seed 是否都能复现**”。
- 当前答案是 `1/2`，不是 `2/2`。

所以从**规则一致性**来看，当前只能 stop。否则就等于在看到 `seed43` 过线后，事后放松了原来写好的决策条件。

#### 4. Why this still does not justify changing smoke gate

从 `smoke200` 到 `600-step` 的变化，确实让人怀疑这条线可能存在某种“late-emerging”特性；但当前证据仍然不够拿来改 gate，原因有三：

1. `smoke200` 在 4 个 seed 上是完全不稳健的；
2. `600-step` 新增复核只得到 `1/2`，没有达到“可复现”门槛；
3. 整个现象发生在 **THUman4 + weak init** 条件下，解释空间仍然很大。

因此，当前最合理的做法是：
- 承认“late-emerging”仍是有信息量的线索；
- 但**不把它升级成规则层面的结论**。

### Problems encountered during this line

| problem | evidence | impact | mitigation | residual risk |
| --- | --- | --- | --- | --- |
| SelfCap 缺少 `masks/` | `data/selfcap_bar_8cam60f` 无法满足 oracle mask 导出前提 | 原始问题无法直接在 SelfCap 上回答 | 改到 `data/thuman4_subject00_8cam60f` | 结果不能直接外推回 SelfCap |
| THUman4 初始化偏弱 | `combine_frames_fast_keyframes.py` 只到 `1/12` keyframes，`match_ratio_over_eligible` 接近 `0` | 可能出现 “rescue-the-brick” 解释 | 在文档里明确标注为 weak-init 现象 | 仍不能代表正常初始化 |
| 早期与后期证据割裂 | smoke200 全 fail，但 600-step 部分 seed 强改善 | 易被误写成“late-emerging 已证实” | 补做 2-seed 600-step 复核 | 复核后仍只有 `1/2` |
| 根仓库与 worktree note 分叉 | 两处 `notes/2026-03-06-thuman4-oracle-weak-decision.md` 内容不同 | 容易引用错文档 | 规定根仓库 note 为唯一事实底稿 | 讨论时仍需提醒不要打开旧副本 |
| `OMP_NUM_THREADS` 告警 | `libgomp: Invalid value for environment variable OMP_NUM_THREADS` | 可能干扰训练稳定性判断 | 显式设置 `OMP_NUM_THREADS=1` | 当前看不影响主结论 |

### Final interpretation after all available evidence

- 这条线在当前证据下**不是 robust early effect**，因为 `4-seed smoke200` 明确失败。
- 这条线也**还不能被升级为 reproducible late-emerging effect**，因为 `600-step` 的新增复核只达到 `1/2`。
- 从描述性统计上看，它又并非纯负例：至少有两个 seed 在 `600-step` 上出现了显著 ROI 改善，且第三个 seed 也有较大 PSNR 向增益，只是没通过感知阈值。
- 因此，最准确的项目状态不是“彻底无效”，而是：
  - **存在后期改善迹象；**
  - **但未满足当前预注册 gate 所要求的可复现强度；**
  - **故当前路线决策仍应为 stop。**

### Practical next-step policy

- 默认动作：**收线**，不再继续投入这条 oracle-weak 线。
- 不做的事：
  - 不改 smoke gate；
  - 不继续扫 `200-step` 权重；
  - 不把 THUman4 结果外推到 SelfCap。
- 唯一保留例外：
  - **只有当上级明确要求时**，才允许补 `seed44` 作为单次 tie-break。
- 如果未来要重启这条线，最有信息量的方向也不是再做同类小扫，而是二选一：
  - 先补齐 SelfCap 的 `masks/` 准备度，回答原始问题；
  - 或在 stronger-init 条件下做一次 sanity check，测试这是否只是 weak-init rescue。

## Expert diagnostic addendum

### Why this addendum exists

- 这一节专门补给同行/专家做**原因诊断**所需的上下文，而不只是做 stop/continue 判断。
- 核心目标不是重复结论，而是尽量减少专家反复追问“mask 的语义到底是什么”“初始化到底有多差”“你们到底有没有中间过程数据”“我该看哪些图”。

### Implementation semantics that experts must see together

#### 1. Oracle pseudo mask is exported as **backgroundness**, not foregroundness

当前 oracle mask 导出器把 dataset silhouette 转成：
- 前景 `fg = 1`
- 背景 `bg = 1 - fg`
- 最终写入 `pseudo_masks.npz` 的是 `bg01`

也就是说，导出的 `masks` 实际语义是：
- **背景 = 1**
- **前景 = 0**

关键实现片段：

```python
fg = (m01 > thr).astype(np.float32)
bg01 = 1.0 - fg
im = Image.fromarray((bg01 * 255.0).astype(np.uint8), mode="L")
```

这意味着当前 oracle 线并不是在给“前景区域打高权重”，而是在给“背景区域提供一个可降权的 oracle 先验”。

#### 2. Trainer-side weak fusion still interprets the slot as a generic mask and applies `w = 1 - alpha * mask`

Trainer 配置文档里的关键定义是：

```python
pseudo_mask_weight: float = 0.0
"""Weak fusion weight alpha for mask-weighted L1.
Interprets pseudo mask as dynamicness in [0,1] and applies:
    w = 1 - alpha * mask
with weighted mean normalization. 0.0 means disabled (baseline behavior)."""
```

因此，把上面的 oracle backgroundness mask 代入后，得到的实际训练权重行为是：
- 前景像素：`mask=0 -> w=1`
- 背景像素：`mask=1 -> w=1-alpha`

在本轮默认参数 `alpha=0.8` 下：
- 前景权重保持 `1.0`
- 背景权重降为 `0.2`

所以本轮实验真正做的是：
- **在整个训练窗口持续压低背景重建损失权重（full-training-window background loss suppression / objective shift）；**
- **前景区域保持正常监督强度。**

#### 3. Oracle weak runner 的默认设置是“强背景降权，持续到 step600”

本轮 oracle wrapper 的关键默认参数为：

```bash
PSEUDO_MASK_WEIGHT="${PSEUDO_MASK_WEIGHT:-0.8}"
PSEUDO_MASK_END_STEP="${PSEUDO_MASK_END_STEP:-600}"
```

且如果 `pseudo_masks.npz` 不存在，会自动从 dataset `masks/` 生成，不存在隐藏的第二条数据准备支线。

#### 4. Why this semantic block is critical for diagnosis

专家在看这条线时，必须把下面三件事同时看到：
- oracle NPZ 语义是 **backgroundness (`bg=1`)**；
- trainer 公式是 **`w = 1 - alpha * mask`**；
- 本轮 `alpha=0.8, end_step=600`。

否则很容易误判为：
- “这是 foreground upweight”，
- 或“这是 generic dynamicness prior”，
- 或“公式和 mask 极性可能完全反了”。

更精确的表述应该是：
- **当前实验是在现有 weak-fusion 槽位里塞入 oracle backgroundness，形成 full-training-window background loss suppression / objective shift。**

### Hard evidence that the initialization is weak

当前“weak init”不是口头判断，而是有机器可读证据支撑。`velocity_stats.json` 的关键内容如下：

```json
{
  "counts": {
    "match_ratio_over_all": 0.0,
    "match_ratio_over_eligible": 0.0,
    "n_points_with_next_frame": 382,
    "n_total_points": 382,
    "n_valid_matches": 0
  },
  "per_pair": [
    {
      "keyframe": 0,
      "match_ratio": 0.0,
      "n_points": 382,
      "n_valid": 0,
      "next_frame": 5,
      "status": "missing_next_points"
    }
  ]
}
```

这说明：
- 参与统计的点并不为零（`n_points_with_next_frame=382`），
- 但有效跨帧匹配为零（`n_valid_matches=0`），
- 所以 `match_ratio_over_eligible=0.0` 不是“没数据”，而是“有候选但没配上”。

这对解释当前结果非常关键，因为它强化了如下诊断假设：
- 当前 THUman4 条件更像是一个**弱初始化 / 弱时序对应**环境；
- 因而 oracle weak 观测到的收益，可能更偏向 **rescue-the-brick**，而不是常规初始化下的普适提升。

### Diagnostic artifact availability: now includes `step399` mid-trajectory

#### Why `seed41` and `seed43`

- 这两个 seed 都是 `seed42` 之外的复核样本，且覆盖了当前最关键的分叉：
  - `seed41`：mixed-evidence seed (gate-fail)；
  - `seed43`：完整过线 seed。
- 结合既有 `step199` 与 `step599` 端点，它们能最小成本补出“中间截面到底发生了什么”。

#### Step399 output root and machine-readable packet

- `step399` 前缀重跑根目录：`.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/`
- 三截面汇总 JSON：`.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/summary/triad_summary.json`

#### `199 / 399 / 599` triad delta table (oracle - baseline)

| seed | step | d_psnr_fg_area | d_lpips_fg_comp | d_psnr_bd_area | d_lpips_bd_comp | d_tlpips |
|---|---:|---:|---:|---:|---:|---:|
| 41 | 199 | +0.088835 | -0.000047 | +0.057479 | -0.000089 | -0.000037 |
| 41 | 399 | +3.071026 | -0.004182 | +1.141049 | -0.002171 | -0.000234 |
| 41 | 599 | +1.580751 | -0.000849 | +0.609282 | -0.000472 | +0.000023 |
| 43 | 199 | +0.094709 | +0.000584 | +0.054605 | -0.000007 | +0.000153 |
| 43 | 399 | +3.124844 | -0.000790 | +1.269454 | -0.002207 | +0.000037 |
| 43 | 599 | +1.678506 | -0.004560 | +0.705789 | -0.000550 | -0.000192 |

#### Mechanism readout after adding `step399`

- 两个 seed 都在 `step399` 就出现了很大的 ROI / boundary PSNR 分离（约 `+3.1` / `+1.2`），说明“分叉并非只在最后一步才出现”。
- 从 `399 -> 599` 看，baseline 本身并没有普遍崩坏，`seed41/43` 的 baseline 前景 PSNR 都继续上升，因此“纯 baseline 中后段失稳 + oracle 单纯幸存”只得到有限支持。
- 真正的分叉更像 LPIPS 转化时序不稳：
  - `seed43`：LPIPS 改善主要在 `599` 才成形；
  - `seed41`：`399` 时 LPIPS 改善较强，但到 `599` 回落到 gate-fail。
- 综合上面三点，当前机制更接近“full-training-window objective shift 下的 seed-dependent LPIPS conversion split”，而非单调的 late-emerging 正效应。

#### What is still missing

- 现在已补齐 `199 / 399 / 599` 三截面，但仍缺少更密的 step-wise 轨迹（例如每 `50` 或 `100` step 一点）。
- 因此可做机制解释增强，但仍不足以单凭这一包去重开 route-level `stop`。

### Minimal visual packet to send reviewers

如果你现在就要把材料发给专家，我建议至少附上下面这些**已存在**的文件路径。这样他们可以直接看原图，不需要再问你“图在哪里”。

#### A. Ground truth / mask anchors (test camera `09`)

- `data/thuman4_subject00_8cam60f/images/09/000000.jpg`
- `data/thuman4_subject00_8cam60f/images/09/000015.jpg`
- `data/thuman4_subject00_8cam60f/images/09/000030.jpg`
- `data/thuman4_subject00_8cam60f/masks/09/000000.png`
- `data/thuman4_subject00_8cam60f/masks/09/000015.png`
- `data/thuman4_subject00_8cam60f/masks/09/000030.png`

#### B. Mixed-evidence seed (gate-fail) (`seed41`) visual triad

**step199**
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/baseline/renders/test_step199_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/oracle_weak/renders/test_step199_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/baseline/renders/test_step199_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/oracle_weak/renders/test_step199_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/baseline/renders/test_step199_0030.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed41/oracle_weak/renders/test_step199_0030.png`

**step399**
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/baseline/renders/test_step399_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/oracle_weak/renders/test_step399_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/baseline/renders/test_step399_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/oracle_weak/renders/test_step399_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/baseline/renders/test_step399_0030.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed41/oracle_weak/renders/test_step399_0030.png`

**step599**
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s41/renders/test_step599_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/renders/test_step599_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s41/renders/test_step599_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/renders/test_step599_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s41/renders/test_step599_0030.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s41/renders/test_step599_0030.png`

#### C. Passing seed (`seed43`) visual triad

**step199**
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/baseline/renders/test_step199_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/oracle_weak/renders/test_step199_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/baseline/renders/test_step199_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/oracle_weak/renders/test_step199_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/baseline/renders/test_step199_0030.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_smoke200_multiseed/seed43/oracle_weak/renders/test_step199_0030.png`

**step399**
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/baseline/renders/test_step399_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/oracle_weak/renders/test_step399_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/baseline/renders/test_step399_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/oracle_weak/renders/test_step399_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/baseline/renders/test_step399_0030.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_step399_diag/seed43/oracle_weak/renders/test_step399_0030.png`

**step599**
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s43/renders/test_step599_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s43/renders/test_step599_0000.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s43/renders/test_step599_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s43/renders/test_step599_0015.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/baseline_s43/renders/test_step599_0030.png`
- `.worktrees/owner-b-20260306-fg-roi-metrics-oracle-weak/outputs/thuman4_oracle_weak_mve/oracle_weak_s43/renders/test_step599_0030.png`

这些对照足够让专家快速判断：
- 轮廓是否真的更干净；
- 背景 suppression 是否换来了纹理/颜色副作用；
- 为什么 `seed41` 在 PSNR 向变好时，`lpips_fg_comp` 仍未达阈值。

### Three concrete questions for external experts

如果你要请同行/专家“分析原因”，建议不要只发材料，还要明确请他们回答下面三类问题：

1. **语义与机制问题**
   - 在当前实现里，把 `bg=1, fg=0` 的 oracle backgroundness mask 塞进 `w = 1 - alpha * mask` 的 weak-fusion 槽位，这个机制本身是否合理？
   - 它更像是在做“full-training-window background loss suppression / objective shift”，还是在滥用一个原本面向 dynamicness 的接口？

2. **结果解释问题**
   - `seed41` 这种“`psnr_fg_area` 明显上涨，但 `lpips_fg_comp` 不够达标”的模式，更像是阈值问题、指标冲突，还是方法本身不稳定？
   - `seed43` 的通过与 `seed41` 的失败之间，最可能的决定性差异是什么？

3. **归因边界问题**
   - 当前现象更像是 **weak-init rescue**，还是已经足够提示某种真实的 late-emerging mechanism？
   - 在 `match_ratio_over_eligible=0.0` 的初始化条件下，当前结果还有多少外推价值？

### Remaining missing diagnostic artifact

即便补完本节，仍有一项对“机制诊断”很重要、但当前材料里还没有的工件：
- **更密的 step-wise masked trajectory**（例如 `199 / 299 / 399 / 499 / 599` 连续 ROI / boundary 曲线，而不止当前 triad）。

所以，如果外部专家在看完当前文档后仍然说“我还差一项信息”，最可能缺的就是：
- **更高时间分辨率的演化轨迹**，而不是更多 seed 的最终端点数字。

## External expert synthesis (v4)

### Scope and status

- 本节汇总 `opinions-a-v4.md` 与 `opinions-b-v4.md` 两份外部诊断意见。
- 目的不是改写 checkpoint 决策，而是把当前最可信的**原因解释、证据边界与后续诊断重点**收拢进同一份主文档。
- 本节**不改变**前文已经写明的路线级结论：当前仍是 **mixed evidence -> stop**。

### High-confidence consensus from both expert reviews

#### 1. Current behavior is more likely **weak-init rescue** than an implementation bug

两份意见都明确支持以下判断：
- 当前现象**不像** `mask` 极性写反、公式弄反、或 weak-fusion 槽位“完全接错”的实现 bug；
- 更像是在弱初始化条件下，通过 `bg=1, fg=0` 的 oracle backgroundness mask 配合 `w = 1 - alpha * mask`，把背景 loss 强烈降权，从而在训练后段“救回”前景 / 轮廓质量；
- 因而更准确的机制表述仍应是：
  - **oracle backgroundness via weak-fusion slot -> full-training-window background loss suppression / objective shift -> possible late rescue under weak init**。

这与前文已经固定的实现语义一致：
- oracle NPZ 是 **backgroundness**；
- trainer 公式是 **`w = 1 - alpha * mask`**；
- 本轮默认是 **`alpha=0.8`、`end_step=600`**。

#### 2. `seed41` is not a trivial negative; it is a **mixed-evidence seed (gate-fail)** blocked by LPIPS conversion

两份意见都把 `seed41` 的解释抓得很准：
- `seed41` 的失败并不是“完全没收益”；
- 它在 `600-step` 下已经出现了明显的 ROI / boundary PSNR 改善：
  - `d_psnr_fg_area=+1.580751`
  - `d_psnr_bd_area=+0.609282`
- 它之所以没过完整 gate，关键不是 ROI 没涨，而是：
  - `d_lpips_fg_comp=-0.000849`
  - 没有跨过 `<= -0.003` 的阈值。

因此，当前更准确的描述不是“2 个正例 + 1 个负例”，而是：
- **2 个完整过线 seed（42/43）**；
- **1 个结构性改善明显、但感知向指标转换不够稳定的 mixed-evidence seed (gate-fail)（41）**。

#### 3. The route-level `stop` decision remains correct

两份意见都认为：
- 当前结果**不是纯负例**，因为 `seed42/43` 在 `600-step` 下已经过线，`seed41` 也有明显 ROI 改善；
- 但它也**还不足以**被升级成“已证实的可复现 late-emerging mechanism”；
- 因为最强、最稳的早期证据仍是：
  - `smoke200` 四个 seed 全不过；
  - 非 42 的 `600-step` 复核结果只有 `replicated = 1/2`。

所以当前 `stop` 的含义应保持为：
- **工程管理上应 stop**；
- **证据上不能把它继续当成正线推进**；
- 但**不能倒写成“已经证伪为纯负例”**。

#### 4. Mid-trajectory triad is now available, but dense trajectory is still missing

两份意见都把当前最大的机制诊断缺口指向同一件事：
- 当前已经有 `step199 / step399 / step599` 三截面；
- 但仍缺少更密的 step-wise 轨迹点；
- 因而目前仍无法彻底区分：
  - 是 baseline 在中后段掉下去、oracle 只是活下来；
  - 还是 oracle 在中后段持续累积增益；
  - 或者只是末段才发生分叉。

因此，**“缺少高时间分辨率 trajectory” 仍是当前最关键的诊断限制**。

### What each expert adds beyond the current note

#### `opinions-a-v4.md` 的主要增量

- 把当前现象明确命名为 **rescue-the-brick / weak-init rescue**，这有助于避免误把它写成“已证实的 late-emerging 正机制”；
- 明确指出 `seed41` 代表的是 **PSNR 有明显收益，但 LPIPS 没稳定跟上** 的指标冲突，而不是“方法无效”；
- 强调当前 `stop` 是**工程管理层面正确的止损动作**；
- 提出一个高信息量的外推性检查方向：
  - **stronger-init sanity check**，用来回答“这是否只是 weak-init rescue”。

#### `opinions-b-v4.md` 的主要增量

- 更明确地把当前问题表述成：
  - **不是 bug**；
  - **不是已站稳的通用 late-emerging mechanism**；
  - 而是 **weak-init 下的晚期 rescue / silhouette clean-up**；
- 把关注点从“有没有 ROI 收益”进一步推进到：
  - **收益类型是否能稳定转化为 gate 所要求的感知向收益**；
- 提出一个很有诊断价值的机制视角：
  - `alpha=0.8` 且 `end_step=max_steps`，使当前设置更像**全训练窗口的 objective shift**，而不是短时 warm-up；
  - 这可以解释为什么 `smoke200` 全不过，但 `600-step` 才开始出现明显 ROI 改善与 seed 分化。

### Important ideas that are still hypotheses, not established facts

以下说法目前都**很有解释力**，但仍应明确写成“假说”，不能升级为已证实事实：

1. **“baseline 在 200 到 600 之间崩掉，而 oracle 只是幸存下来”**
   - 这是强假说；
   - 即便已有 `step399`，没有更密曲线仍不能直接证明。

2. **“当前现象主要由 `alpha=0.8 + end_step=max_steps` 的全程 objective shift 驱动”**
   - 这是合理推断；
   - 但当前还没有 `alpha` / `end_step` 消融来把它钉死。

3. **“这条线对正常初始化没有价值，只对 weak-init rescue 有价值”**
   - 这是目前最值得优先检验的外推性假说；
   - 但在 stronger-init 条件下还没有直接 sanity check 结果前，不能把它写成定论。

### Recommended wording for future discussions

如果后续要与同行/专家或上级讨论，这条线最稳妥的单句表述建议统一为：

- **当前 oracle backgroundness weak-fusion 不是 robust early effect，也还不是已证实的 late-emerging mechanism；它更像 weak-init 条件下、由强背景降权带来的 late rescue 线索：在当前 3 个已审计的 600-step seeds 中，ROI PSNR 一致大幅上升，boundary PSNR 同向为正，但 LPIPS 向改善的转化不稳，因此在 replication rule 下仍应维持 route-level `stop`。**

### What this synthesis changes and what it does not change

这两份 `v4` 专家意见带来的主要变化是：
- **提高了对“原因解释”的把握度**；
- **提高了对“当前不像实现 bug”的信心**；
- **提高了对“seed41 应视为 mixed-evidence seed (gate-fail)，而非简单负例”的表述精度**。

但它们**没有**改变以下三点：
- 不改当前 smoke gate；
- 不把这条线升级为可继续 line-level 投入的正线；
- 不把 THUman4 / weak-init 下的现象直接外推回 SelfCap 或正常初始化场景。
