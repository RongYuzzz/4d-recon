# OpenProposal Phase 4 (THUman4.0) — VGGT Feature Metric / Correspondence Loss Implementation Plan

> **Execution note:** 按 Task 顺序逐条执行；每个 Task 的 Expected 通过后再进入下一步。

**Goal:** 在 THUman 子集上落地一条“跑得动、算得清、可解释”的 VGGT feature/correspondence 约束，并尽可能提升 4D 重建常用指标 **PSNR/LPIPS（尤其 fg-masked: `psnr_fg/lpips_fg`）**；若未提升，也要产出可解释的 failure boundary + 排查记录。

**Architecture:** 本 Phase 对齐总计划 `docs/plans/2026-03-02-align-opening-proposal-v1.md` 的 Phase 4（不得与其矛盾）。实现顺序写死：**优先跑通 Plan‑B + VGGT feature metric loss（现有脚本）**，再做 1 次小幅迭代（最多改 1 个变量），然后止损。对应可视化复用 `scripts/viz_tokenproj_temporal_topk.py`（从 VGGT cache 画 top‑k token 匹配）。

**Tech Stack:** `scripts/run_train_planb_feature_loss_v2_selfcap.sh`, `scripts/precompute_vggt_cache.py`, `scripts/viz_tokenproj_temporal_topk.py`, `scripts/eval_masked_metrics.py`, `pytest`。

**2026-03-04 状态更新（来自 Phase 3，影响 Phase 4 的默认策略）：**
- Phase 3 的 weak-fusion 在本 scene 上出现“**full-frame 小幅提升，但 fg-masked 退化**”（详见 `notes/openproposal_phase3_weak_supervision_result.md`）。
- 因此本 Phase 4 的成功口径以 **`psnr_fg/lpips_fg` 为主**；full-frame 只作参考，避免重复落入“全图更好但前景更差”的陷阱。
- 本 Phase 4 默认开启 **`VGGT_FEAT_GATING=framediff`**：用帧差 top‑p gate 让 feature loss 更聚焦于变化区域（更接近前景/动态区域的目标口径）。`gating='cue'` 在当前代码里 **未实现**，不要选。

---

### Task 0: Gate Check（Phase 1/3 baseline 就绪）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 确认 baseline anchor**

Run:
```bash
test -f outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats/test_step0599.json || echo "[WARN] baseline planb_init_600 missing; run Phase 1 planb_init_600 first"
```

Expected: 通过

**Step 2: 确认 masked evaluator 可用**

Run:
```bash
python3 -c "import importlib.util; import pathlib; p=pathlib.Path('scripts/eval_masked_metrics.py'); assert p.exists(); print('ok')"
```

Expected: `ok`

---

### Task 1: VGGT 权重与 cache preflight（避免训练中途卡下载）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 固定模型与 cache 目录（本机，不入库）**

```bash
export OMP_NUM_THREADS=1  # 避免 libgomp “OMP_NUM_THREADS=0” 警告刷屏
export VGGT_MODEL_ID="facebook/VGGT-1B"
export VGGT_CACHE_DIR="/root/autodl-tmp/cache/vggt"
export VGGT_MODEL_CACHE_DIR="$VGGT_CACHE_DIR"  # runner/precompute uses this name
mkdir -p "$VGGT_CACHE_DIR"
```

**Step 2: 若未 warmup，先做一次最小加载**

推荐优先离线自检；若本机尚无缓存再临时在线一次下载：

离线自检（优先）：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; VGGT.from_pretrained('$VGGT_MODEL_ID', cache_dir='$VGGT_MODEL_CACHE_DIR'); print('ok')"
```

若失败（cache 不完整/不存在）→ 临时在线一次下载：
```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"
HF_HUB_OFFLINE=0 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" -c "from vggt.models.vggt import VGGT; VGGT.from_pretrained('$VGGT_MODEL_ID', cache_dir='$VGGT_MODEL_CACHE_DIR'); print('ok')"
```

Expected: 打印 `ok`

---

### Task 2: 跑 Plan‑B + FeatureLoss‑v2（主实验）

**Files:**
- Modify: *(none)*
- Create: *(none)*
- Test: *(none)*

**Step 1: 冻结 cache tag（避免与 SelfCap 混淆）**

建议（示例）：
```bash
export VGGT_CACHE_TAG="openproposal_thuman4_s00_tokenproj_l17_d32_s20260225_f0_n60_cam8_ds4_fd0.10"
export VGGT_CACHE_OUT_DIR="outputs/vggt_cache/$VGGT_CACHE_TAG"
```

**Step 2（推荐）：先独立预计算 cache（失败更早暴露；不依赖训练脚本）**

> 若 `$VGGT_CACHE_OUT_DIR/gt_cache.npz` 已存在，可跳过。

Run：
```bash
DATA_DIR="data/thuman4_subject00_8cam60f"

REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
"$VENV_PYTHON" scripts/precompute_vggt_cache.py \
  --data_dir "$DATA_DIR" \
  --out_dir "$VGGT_CACHE_OUT_DIR" \
  --camera_ids "02,03,04,05,06,07,08,09" \
  --frame_start 0 \
  --num_frames 60 \
  --backend vggt \
  --phi_name token_proj \
  --phi_downscale 4 \
  --token_layer_idx 17 \
  --token_proj_dim 32 \
  --token_proj_seed 20260225 \
  --token_proj_normalize 1 \
  --save_framediff_gate 1 \
  --framediff_top_p 0.10 \
  --vggt_model_id "$VGGT_MODEL_ID" \
  --vggt_cache_dir "$VGGT_MODEL_CACHE_DIR" \
  --vggt_mode crop
```

Expected:
- `outputs/vggt_cache/$VGGT_CACHE_TAG/gt_cache.npz`
- `outputs/vggt_cache/$VGGT_CACHE_TAG/meta.json`

**Step 3: 启动训练（Plan‑B init + feature metric loss）**

Run（只改 DATA_DIR/RESULT_DIR，其余先用 conservative defaults；允许你把 GPU 改成空闲卡）：
```bash
DATA_DIR="data/thuman4_subject00_8cam60f" \
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600" \
GPU=1 MAX_STEPS=600 \
VENV_PYTHON="${VENV_PYTHON:-$(pwd)/third_party/FreeTimeGsVanilla/.venv/bin/python}" \
VGGT_MODEL_ID="$VGGT_MODEL_ID" \
VGGT_MODEL_CACHE_DIR="$VGGT_MODEL_CACHE_DIR" \
VGGT_CACHE_TAG="$VGGT_CACHE_TAG" \
VGGT_CACHE_OUT_DIR="$VGGT_CACHE_OUT_DIR" \
VGGT_FEAT_PHI_NAME="token_proj" \
VGGT_FEAT_LOSS_TYPE="cosine" \
LAMBDA_VGGT_FEAT="0.01" \
VGGT_FEAT_START_STEP="0" \
VGGT_FEAT_RAMP_STEPS="400" \
VGGT_FEAT_EVERY="8" \
VGGT_FEAT_GATING="framediff" \
VGGT_FEAT_GATING_TOP_P="0.10" \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

Expected:
- `outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600/stats/test_step0599.json`
- `outputs/vggt_cache/$VGGT_CACHE_TAG/gt_cache.npz`

**Step 4: 训练完成后，先做最小 sanity（不读大文件）**

Run:
```bash
test -f outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600/cfg.yml
test -f outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600/stats/test_step0599.json
```

可选（强烈推荐）：确认 feature loss 确实开启、且 gating 按预期：
```bash
rg -n \"lambda_vggt_feat|vggt_feat_gating|vggt_feat_cache_npz\" \
  outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600/cfg.yml
```

---

### Task 3: 对齐口径评测（psnr_fg/lpips_fg）+ Guardrail（ΔtLPIPS）

**Files:**
- Create: `notes/openproposal_phase4_attention_contrastive.md`
- Modify: *(none)*
- Test: *(none)*

**Step 1: baseline masked eval**

```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto
```

Fallback（若本机 venv 没有 torch+lpips）：
```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend dummy
```

**Step 2: feature-loss masked eval**

```bash
REPO_ROOT="$(pwd)"
VENV_PYTHON="${VENV_PYTHON:-$REPO_ROOT/third_party/FreeTimeGsVanilla/.venv/bin/python}"

"$VENV_PYTHON" scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend auto
```

Fallback（若本机 venv 没有 torch+lpips）：
```bash
python3 scripts/eval_masked_metrics.py \
  --data_dir data/thuman4_subject00_8cam60f \
  --result_dir outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600 \
  --stage test \
  --step 599 \
  --mask_source dataset \
  --bbox_margin_px 32 \
  --lpips_backend dummy
```

**Step 2.5（推荐）：避免覆盖写入导致混淆，做一次拷贝锁定**

> `eval_masked_metrics.py` 输出路径固定为 `stats_masked/test_step0599.json`。为避免后续改 margin/thr 时误覆盖，建议复制一份带后缀的快照。

```bash
cp outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599.json \
  outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats_masked/test_step0599_phase4.json

cp outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600/stats_masked/test_step0599.json \
  outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600/stats_masked/test_step0599_phase4.json
```

**Step 3: Guardrail 检查（tLPIPS 不得显著变差）**

手工从两个 `stats/test_step0599.json` 抽取 `tlpips`：
- 目标：尽量满足 `ΔtLPIPS <= +0.01`（如果做不到，必须写 trade-off + 归因）

可选（自动算 delta）：
```bash
python3 - <<'PY'
import json
def load(path: str):
  with open(path, encoding="utf-8") as f:
    return json.load(f)
b = load("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600/stats/test_step0599.json").get("tlpips")
t = load("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_600/stats/test_step0599.json").get("tlpips")
if b is None or t is None:
  raise SystemExit("missing tlpips in one of the stats jsons (check eval_on_test and eval_sample_every_test=1)")
print("tlpips_baseline", b)
print("tlpips_treat   ", t)
print("delta          ", float(t) - float(b))
PY
```

**Step 3.5（推荐）：一键打印 full + fg 指标与 deltas（避免手抄出错）**

```bash
python3 - <<'PY'
import json
from pathlib import Path

baseline = Path("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_init_600")
treat = Path("outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_600")

def load(p: Path):
  return json.load(open(p, encoding="utf-8"))

bf = load(baseline/"stats/test_step0599.json")
tf = load(treat/"stats/test_step0599.json")
bm = load(baseline/"stats_masked/test_step0599.json")
tm = load(treat/"stats_masked/test_step0599.json")

keys_full = ["psnr","ssim","lpips","tlpips"]
keys_fg = ["psnr_fg","lpips_fg","num_fg_frames"]

print("== full")
for k in keys_full:
  print(k, "baseline=", bf.get(k), "treat=", tf.get(k), "delta=", (tf.get(k) - bf.get(k)) if (bf.get(k) is not None and tf.get(k) is not None) else None)
print("== fg-masked")
for k in keys_fg:
  bv, tv = bm.get(k), tm.get(k)
  d = (tv - bv) if (isinstance(bv,(int,float)) and isinstance(tv,(int,float))) else None
  print(k, "baseline=", bv, "treat=", tv, "delta=", d)
PY
```

**Step 4: 写 Phase 4 结论文档**

在 `notes/openproposal_phase4_attention_contrastive.md` 中写清：
- baseline vs planb_feat_v2 两条路径
- 关键超参（`lambda_vggt_feat`, `vggt_feat_*`、cache tag、mask eval 口径）
- full-frame vs fg-masked 指标对照
- Guardrail（tLPIPS）是否满足
- 若未提升：按总计划的排查顺序给出 3–5 条具体排查结论（不要泛泛而谈）

**Step 5: Commit（仅文档）**

```bash
git add notes/openproposal_phase4_attention_contrastive.md
git commit -m "docs(notes): Phase4 feature-metric loss result + guardrail"
```

---

### Task 4: 对应可解释证据（top‑k token 匹配可视化）

**Files:**
- Modify: `notes/openproposal_phase4_attention_contrastive.md`
- Create: *(none)*
- Test: *(none)*

**Step 1: 生成 top‑k 可视化**

Run:
```bash
python3 scripts/viz_tokenproj_temporal_topk.py \
  --cache_npz "outputs/vggt_cache/$VGGT_CACHE_TAG/gt_cache.npz" \
  --out_dir "outputs/qualitative_local/openproposal_phase4/tokenproj_topk" \
  --frames "0,30" \
  --topk 30 \
  --camera_ids "09" \
  --cell 48
```

Expected:
- `outputs/qualitative_local/openproposal_phase4/tokenproj_topk/*.jpg` 存在（本机可打开）

**Step 2: 在 Phase 4 文档里引用本机路径（不打包、不入证据链）**

---

### Task 5: 一次且仅一次的小迭代（可选；严格止损）

> 规则：只改 1 个变量，且最多 1 次迭代；否则 Phase 4 变成无底洞。

**Files:**
- Modify: `notes/openproposal_phase4_attention_contrastive.md`
- Create: *(none)*
- Test: *(none)*

**Step 1: 选择一个改动方向（只选其一）**

建议优先顺序（从“最像安全工程”到“更冒险”）：
1) 降低 `LAMBDA_VGGT_FEAT`（例如 0.01 → 0.005）
2) 推迟 `VGGT_FEAT_START_STEP`（例如 0 → 100）
3) 增大 `VGGT_FEAT_RAMP_STEPS`（例如 400 → 800）

**Step 2: 复跑一次（新 result_dir，append-only）**

示例（仅示意，按你选的 1 个变量替换）：
```bash
DATA_DIR="data/thuman4_subject00_8cam60f" \
RESULT_DIR="outputs/protocol_v3_openproposal/thuman4_subject00_8cam60f/planb_feat_v2_gatediff0.10_lam0.005_600" \
GPU=1 MAX_STEPS=600 \
LAMBDA_VGGT_FEAT=0.005 \
VENV_PYTHON="${VENV_PYTHON:-$(pwd)/third_party/FreeTimeGsVanilla/.venv/bin/python}" \
VGGT_MODEL_ID="$VGGT_MODEL_ID" \
VGGT_MODEL_CACHE_DIR="$VGGT_MODEL_CACHE_DIR" \
VGGT_CACHE_TAG="$VGGT_CACHE_TAG" \
VGGT_CACHE_OUT_DIR="$VGGT_CACHE_OUT_DIR" \
VGGT_FEAT_PHI_NAME="token_proj" \
VGGT_FEAT_LOSS_TYPE="cosine" \
VGGT_FEAT_START_STEP="0" \
VGGT_FEAT_RAMP_STEPS="400" \
VGGT_FEAT_EVERY="8" \
VGGT_FEAT_GATING="framediff" \
VGGT_FEAT_GATING_TOP_P="0.10" \
HF_HUB_OFFLINE=1 HF_HUB_DISABLE_XET=1 \
bash scripts/run_train_planb_feature_loss_v2_selfcap.sh
```

**Step 3: 重复 Task 3 的评测 + 文档补充**

---

## Exit Criteria（Phase 4 验收）

- 至少给出一个可审计结论（提升或失败边界都可）：
  - 优先：`lpips_fg` ↓ 且 `psnr_fg` ↑（同一步数、同协议口径）
  - 若只能提升其一：必须写 trade-off（含 `ΔtLPIPS`）
- 对应可视化存在（top‑k token match），并能在答辩时解释“在对齐什么”
- 若失败：文档包含明确止损点 + 下一步可执行改法（但 Phase 4 本身停止扩展）
