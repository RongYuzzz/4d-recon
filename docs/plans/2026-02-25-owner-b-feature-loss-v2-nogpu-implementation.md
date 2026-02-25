# Owner B: Feature-Loss v2 (No-GPU) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不占用 GPU 的前提下，把 Feature Metric Loss v2 的“可执行工程对象”落到仓库：v2 runner 脚本、sanity 脚本、trainer v2（token-proj + cosine + ramp + framediff gating）与 cache v2（token-proj + gate），并更新 scoreboard 使 v2 结果能进入证据链。交付到 `main` 后，Owner A 可直接按 `docs/execution/2026-02-26-feature-loss-v2.md` 用 GPU0 执行 M1/M2。

**Architecture:** 以 `protocol_v1` 为唯一可比协议。v2 的核心是：用 VGGT 的 **Aggregator patch tokens**（低分辨率、抗对齐误差）作为“stride~16 的中间层特征”，通过 **固定随机投影**压缩通道（避免 cache 过大），对 render/GT 特征做 `normalize + cosine`，并用 **framediff top‑p% gating** 将 patch 采样聚焦到动态/困难区域。所有新逻辑默认关闭，v1 行为不回归。

**Tech Stack:** Python（tyro/torch/numpy）、Bash、VGGT（冻结推理）、FreeTimeGsVanilla trainer、现有 report-pack/evidence 工具链。

---

## Task B1: 建立隔离工作区（不改 main 直接开发）

**Files:**
- N/A

**Step 1: 创建 worktree**

Run:
```bash
cd /root/projects/4d-recon
git fetch origin
git worktree add .worktrees/owner-b-20260225-featureloss-v2-nogpu origin/main
cd .worktrees/owner-b-20260225-featureloss-v2-nogpu
```
Expected: worktree 创建成功，`git status` 干净。

---

## Task B2: 先写失败测试（确保 v2 交付面“被锁死”）

**Files:**
- Create: `scripts/tests/test_feature_loss_v2_artifacts_exist.py`
- Modify: `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 写一个失败测试，要求 v2 关键脚本必须存在**

Create `scripts/tests/test_feature_loss_v2_artifacts_exist.py`（示例）：
```python
#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    REPO_ROOT / "scripts" / "run_train_feature_loss_v2_selfcap.sh",
    REPO_ROOT / "scripts" / "run_train_feature_loss_v2_gated_selfcap.sh",
    REPO_ROOT / "scripts" / "check_vggt_preprocess_consistency.py",
]

def run_test() -> None:
    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        raise AssertionError("missing v2 artifacts: " + ", ".join(str(p) for p in missing))
    for p in REQUIRED[:2]:
        # shell scripts should be executable (or at least readable); keep check minimal.
        if not os.access(p, os.R_OK):
            raise AssertionError(f"not readable: {p}")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        sys.exit(1)
    print("PASS: v2 artifacts exist")
```

**Step 2: 运行测试，确认先失败**

Run:
```bash
cd /root/projects/4d-recon/.worktrees/owner-b-20260225-featureloss-v2-nogpu
python3 scripts/tests/test_feature_loss_v2_artifacts_exist.py
```
Expected: FAIL（因为脚本尚未创建）。

**Step 3: 扩展 scoreboard 单测，使其不会忽略 v2 运行名**

说明：当前 `scripts/summarize_scoreboard.py` 只收录 `feature_loss_v1*`。v2 合入后，scoreboard 必须能显示 `feature_loss_v2*_600`。

Modify `scripts/tests/test_summarize_scoreboard.py`：
- 添加一条 `run_dir=outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_600` 的 synthetic row
- 断言 scoreboard 输出包含 `feature_loss_v2_600`

**Step 4: 运行单测，确认失败（因为 summarize_scoreboard 尚未更新）**

Run:
```bash
python3 scripts/tests/test_summarize_scoreboard.py
```
Expected: FAIL（直到实现 v2 选择逻辑）。

---

## Task B3: 添加 v2 runner 脚本（无 GPU 可完成）

**Files:**
- Create: `scripts/run_train_feature_loss_v2_selfcap.sh`
- Create: `scripts/run_train_feature_loss_v2_gated_selfcap.sh`

**Step 1: 复制 v1 runner 结构，写 v2 runner（无 gating）**

Create: `scripts/run_train_feature_loss_v2_selfcap.sh`

要求（必须满足）：
- 默认输出目录：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_600`
- 默认 `GPU=${GPU:-1}`（但 A 会用 `GPU=0` 覆盖）
- 默认 `MAX_STEPS=600`
- feature-loss 必须开启 cosine + warmup/ramp（对应 v2 trainer flags）
- 默认 phi 选择为 v2（建议：`token_proj`），并把 projection 参数写入 cache（seed/dim/layer）
- 训练结束后写 `stats/throughput.json`（从 `stats/train_stepXXXX.json` 推导 iter/s）

**Step 2: 写 v2_gated runner（framediff gating）**

Create: `scripts/run_train_feature_loss_v2_gated_selfcap.sh`

要求：
- 默认输出目录：`outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_gated_600`
- 默认 gating：`framediff` + `top_p=0.10`（可通过 env 覆盖）

**Step 3: shell 语法检查**

Run:
```bash
bash -n scripts/run_train_feature_loss_v2_selfcap.sh
bash -n scripts/run_train_feature_loss_v2_gated_selfcap.sh
```
Expected: PASS。

**Step 4: 重新跑 Task B2 的存在性测试**

Run:
```bash
python3 scripts/tests/test_feature_loss_v2_artifacts_exist.py
```
Expected: 仍 FAIL（因为 sanity 脚本还没写）。

**Step 5: 提交**

Run:
```bash
git add scripts/run_train_feature_loss_v2_selfcap.sh scripts/run_train_feature_loss_v2_gated_selfcap.sh
git commit -m "scripts: add feature-loss v2 runners (protocol_v1 paths)"
```

---

## Task B4: 新增 sanity 脚本（GT self-consistency + cache round-trip）

**Files:**
- Create: `scripts/check_vggt_preprocess_consistency.py`
- Create: `scripts/tests/test_vggt_preprocess_consistency_dummy.py`

**Step 1: 先写失败测试（dummy 模式，不依赖 vggt 包）**

Create `scripts/tests/test_vggt_preprocess_consistency_dummy.py`：
- 生成 tiny dataset（复用 `test_vggt_cache_contract.py` 的造数据方式）
- 调用 `scripts/check_vggt_preprocess_consistency.py --backend dummy ...`
- 期望 returncode=0，并输出包含 `PASS`

**Step 2: 运行测试，确认失败（脚本未实现或不支持 dummy）**

Run:
```bash
python3 scripts/tests/test_vggt_preprocess_consistency_dummy.py
```
Expected: FAIL。

**Step 3: 实现 sanity 脚本（至少支持 dummy；vggt 可选）**

Create `scripts/check_vggt_preprocess_consistency.py`，最小要求：
- 支持 `--backend dummy|vggt`（dummy 用简单下采样特征）
- 支持输入 `--data_dir ... --camera_ids ... --frame_start ... --num_frames ...`
- 产出：
  - GT self-consistency：同一图像跑两次，差值应接近 0（给阈值）
  - cache round-trip：调用 `scripts/precompute_vggt_cache.py` 生成 cache 后，比较 cache 读出与在线计算的一致性
- 输出 PASS/FAIL（用于 A 的 Gate M1 前置检查）

**Step 4: 跑测试，确认 PASS**

Run:
```bash
python3 scripts/tests/test_vggt_preprocess_consistency_dummy.py
python3 scripts/tests/test_feature_loss_v2_artifacts_exist.py
```
Expected: 两个测试都 PASS（v2 三个关键脚本齐了）。

**Step 5: 提交**

Run:
```bash
git add scripts/check_vggt_preprocess_consistency.py scripts/tests/test_vggt_preprocess_consistency_dummy.py scripts/tests/test_feature_loss_v2_artifacts_exist.py
git commit -m "scripts: add v2 preprocess consistency sanity (dummy) and tests"
```

---

## Task B5: trainer v2：token-proj phi + cosine + ramp + framediff gating（默认关闭，v1 不回归）

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Modify: `scripts/tests/test_vggt_feature_loss_flags.py`
- Create: `scripts/tests/test_vggt_feat_v2_flag_tokens.py`

**Step 1: 写失败测试，锁定 v2 必须出现的 tokens/flags**

Create `scripts/tests/test_vggt_feat_v2_flag_tokens.py`：
- 读取 trainer 源码
- 断言包含关键标记字符串（示例）：
  - `token_proj`
  - `vggt_feat_loss_type`
  - `vggt_feat_ramp_steps`
  - `vggt_feat_gating_top_p`
  - `gate_framediff`

Run:
```bash
python3 scripts/tests/test_vggt_feat_v2_flag_tokens.py
```
Expected: FAIL（尚未实现）。

**Step 2: 修改 config/dataclass，增加 v2 控制项（默认不改变 v1）**

在 trainer Config 中新增字段（建议默认值）：
- `vggt_feat_loss_type: Literal["l1","cosine"] = "l1"`
- `vggt_feat_ramp_steps: int = 0`
- `vggt_feat_gating_top_p: float = 0.10`

并把 `vggt_feat_phi_name` 的合法值扩展为：`depth|world_points|token_proj`。

**Step 3: 实现 token-proj phi_render（不依赖 VGGT forward dict）**

实现逻辑（建议最小可用）：
- 当 `phi_name == "token_proj"`：
  - 调用 `self.vggt_feat_model.aggregator(images_1xSx3xHxW)` 得到 `aggregated_tokens_list, patch_start_idx`
  - 取 `layer_idx` / `proj_dim` / `proj_seed`（从 cache NPZ 中读取，避免 cfg 漂移）
  - 提取 patch tokens reshape 成 `[S, 2C, Hpatch, Wpatch]`
  - 生成固定随机投影矩阵 `W`（seed 固定；存为 trainer attribute；requires_grad=False）
  - `phi = einsum(W, tokens)` 得到 `[S, proj_dim, Hpatch, Wpatch]`

注意：
- **禁止 `torch.no_grad()`** 包裹 render 分支 aggregator（保证梯度链）
- autocast 保持与 v1 一致即可

**Step 4: 把 feature loss 从 L1 扩展为 cosine（v2 默认走 cosine）**

实现建议：
- 统一先构造 per-pixel scalar map（`[B,1,Hf,Wf]`）
- cosine：`1 - sum(F_pred_n * F_gt_n, dim=1, keepdim=True)`
- L1：先 abs 再 mean over channel 到 `[B,1,Hf,Wf]`

加 ramp：
- 若 `vggt_feat_ramp_steps>0`：`lambda_eff = lambda * clamp((step-start)/ramp, 0..1)`

**Step 5: 实现 framediff gating（cache 优先，缺失则 warning 并回退 none）**

约定：
- cache NPZ 可选含 `gate_framediff`，shape `[T,V,1,Hf,Wf]`，uint8/float16 都可
- trainer `_get_vggt_feat_targets` 同步取出 gate（按 frame/cam 索引）
- patch 采样/weight_map 乘上 gate，实现 top‑p% 的“动态候选区域”

**Step 6: 运行全量脚本测试（不跑训练）**

Run:
```bash
python3 scripts/tests/test_vggt_feature_loss_flags.py
python3 scripts/tests/test_vggt_feat_v2_flag_tokens.py
python3 scripts/tests/test_*.py
```
Expected: 全 PASS。

**Step 7: 提交**

Run:
```bash
git add third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py scripts/tests/test_vggt_feature_loss_flags.py scripts/tests/test_vggt_feat_v2_flag_tokens.py
git commit -m "feat(vggt): add feature-loss v2 (token-proj, cosine+ramp, framediff gating)"
```

---

## Task B6: cache v2：支持 token-proj + framediff gate + normalized 存盘（不影响 dummy contract）

**Files:**
- Modify: `scripts/precompute_vggt_cache.py`
- Modify: `scripts/tests/test_vggt_cache_contract.py`
- Create: `scripts/tests/test_token_proj_determinism.py`

**Step 1: 写失败测试，验证 token-proj 投影确定性（纯 CPU，不依赖 vggt）**

Create `scripts/tests/test_token_proj_determinism.py`：
- 构造随机 tokens（固定 seed）
- 调用你新增的投影 helper（建议放在 `scripts/precompute_vggt_cache.py` 内部函数或独立 util）
- 断言相同 seed 输出一致，不同 seed 输出不同

Run:
```bash
python3 scripts/tests/test_token_proj_determinism.py
```
Expected: FAIL（helper 未实现）。

**Step 2: 修改 precompute 脚本，增加 `phi_name=token_proj` 路径**

要求：
- 仍保留 v1：`depth/world_points` 不变
- token-proj 分支：
  - 调用 `VGGT.aggregator` 获取 tokens（不跑 head）
  - 生成投影后输出 `phi`（建议 float16）
  - 存入 NPZ 额外 key：
    - `token_layer_idx`、`token_proj_dim`、`token_proj_seed`、`phi_is_normalized`
    - `gate_framediff`（若启用 framediff gate；建议默认启用并写入 top_p 到 meta）
- meta.json 增补上述字段（便于审计）

**Step 3: framediff gate 生成（top‑p%，不靠阈值）**

实现建议（cache 阶段做，训练不做 IO）：
- 在 VGGT preprocess 后的输入空间生成灰度图
- per-frame normalize 或轻微 blur 后做 abs diff
- 以 patch_size 对齐下采样到 phi-space（例如 14x14 pool -> 37x37）
- 对每 view 计算 top‑p% mask，并存入 `gate_framediff`

**Step 4: 维持 dummy contract 测试不回归**

更新 `scripts/tests/test_vggt_cache_contract.py`：
- 不新增 required keys（保持原 contract）
- 允许新增可选 key（不做断言）

**Step 5: 跑测试**

Run:
```bash
python3 scripts/tests/test_vggt_cache_contract.py
python3 scripts/tests/test_token_proj_determinism.py
```
Expected: PASS。

**Step 6: 提交**

Run:
```bash
git add scripts/precompute_vggt_cache.py scripts/tests/test_vggt_cache_contract.py scripts/tests/test_token_proj_determinism.py
git commit -m "feat(cache): add token-proj phi and framediff gate metadata (v2)"
```

---

## Task B7: scoreboard 收录 v2 变体（让 A 的 v2 结果能进证据链）

**Files:**
- Modify: `scripts/summarize_scoreboard.py`
- Modify: `scripts/tests/test_summarize_scoreboard.py`

**Step 1: 修改 scoreboard 选择逻辑**

在 `scripts/summarize_scoreboard.py`：
- 扩展 `_is_feature_loss_variant`：匹配 `feature_loss_v2` 与 gated/其他后缀（仅 full600，不收 smoke）
- 确保 run order：v1/v2 都排在 feature-loss 区域内

**Step 2: 跑单测（应从 FAIL 变 PASS）**

Run:
```bash
python3 scripts/tests/test_summarize_scoreboard.py
```
Expected: PASS（包含 `feature_loss_v2_600`）。

**Step 3: 提交**

Run:
```bash
git add scripts/summarize_scoreboard.py scripts/tests/test_summarize_scoreboard.py
git commit -m "fix(scoreboard): include feature-loss v2 variants in selection"
```

---

## Task B8: 合并到 main + 通知 A 开始跑 GPU0（M1/M2）

**Files:**
- N/A

**Step 1: 最终测试**

Run:
```bash
python3 scripts/tests/test_*.py
bash -n scripts/run_train_feature_loss_v2_selfcap.sh
bash -n scripts/run_train_feature_loss_v2_gated_selfcap.sh
```
Expected: 全 PASS。

**Step 2: push 到 main**

Run:
```bash
git push origin HEAD:main
```
Expected: push 成功。

**Step 3: 给 A 的交接口径（复制粘贴即可）**

发送给 A：
- 已合入：v2 runner + sanity + trainer v2 + cache v2 + scoreboard
- A 从 main 执行：
  - `GPU=0 MAX_STEPS=200 RESULT_TAG=feature_loss_v2_smoke200 bash scripts/run_train_feature_loss_v2_selfcap.sh`
  - `GPU=0 MAX_STEPS=200 RESULT_TAG=feature_loss_v2_gated_smoke200 bash scripts/run_train_feature_loss_v2_gated_selfcap.sh`
  - M1 PASS 后再跑两次 full600（v2 与 v2_gated）

