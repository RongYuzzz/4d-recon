# Owner B: Fix v2 token_proj Downscale Mismatch + M1 Playbook (No-GPU) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 feature-loss v2 的一个高风险一致性 bug（`token_proj` 在 cache 使用 `phi_downscale` 下采样，但 trainer 侧未做同等下采样，导致 phi_render/phi_gt 严重错位），并补齐最小“可比 M1”跑法文档与 runner 默认参数（减少 A 再次 M1 灾难性退化的概率）。全程不占用 GPU。

**Architecture:** 在 `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py` 中把 `token_proj` 的 phi_render 计算改为：先按原 patch 网格（37x37）投影，再用 `F.interpolate(mode=bilinear, align_corners=False)` resize 到 cache 的 `phi_size`（与 `scripts/precompute_vggt_cache.py::_downscale_vchw` 对齐）。用 CPU 单测锁死该行为。最后更新 runner 默认值（更保守）与 `docs/execution/2026-02-26-feature-loss-v2.md` 的 M1 指南（要求 smoke200 对齐 baseline_smoke200，而不是 baseline_600）。

**Tech Stack:** Python（torch/numpy）、Bash（runner）、现有 scripts/tests。

---

### Task B1: 先写失败测试，锁死 “token_proj 必须 resize 对齐 cache phi_size”

**Files:**
- Create: `scripts/tests/test_token_proj_resize_alignment.py`

**Step 1: 写测试（不依赖 vggt 权重，不跑训练）**

Create `scripts/tests/test_token_proj_resize_alignment.py`：
- 构造随机 `patch_tokens`（形状 `[S,Npatch,D]`，其中 `S=8, patch_h0=37, patch_w0=37, Npatch=1369`）
- 构造固定投影矩阵 `W:[proj_dim,D]`（`proj_dim=32`）
- 计算 reference：
  - 先 `einsum` 投影得到 `[S,proj_dim,37,37]`
  - 再 `F.interpolate` 到 `[S,proj_dim,hf,wf]`（例如 `hf=9,wf=9`，对应 `phi_downscale=4`）
- 调用 trainer 内的新 helper（B2 会实现）得到实际输出
- 断言 max_abs_diff < 1e-5

**Step 2: 运行测试，确认先 FAIL（因为 helper 未实现）**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_token_proj_resize_alignment.py
```
Expected: FAIL（ImportError 或 missing function）。

---

### Task B2: 修复 trainer：token_proj 先投影再 resize（替代“截断前 hf*wf tokens”）

**Files:**
- Modify: `third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py`
- Modify: `scripts/tests/test_vggt_feat_v2_flag_tokens.py`（如需补 token）

**Step 1: 在 trainer 中新增纯函数/静态 helper（可被测试直接调用）**

建议加在 trainer 文件内（类外或类内 `@staticmethod` 均可）：
- 输入：
  - `patch_tokens_snd: Tensor`（`[S,Npatch,D]`）
  - `w: Tensor`（`[proj_dim,D]`）
  - `patch_h0, patch_w0`（原 patch 网格，例如 37x37）
  - `hf, wf`（cache phi_size）
- 输出：`phi: Tensor`（`[S,proj_dim,hf,wf]`）
- 实现：`einsum` 后 reshape 到 `[S,proj_dim,patch_h0,patch_w0]`，再 `F.interpolate` 到 `(hf,wf)`（bilinear/align_corners=False）

**Step 2: 修改 `_compute_vggt_token_proj_phi` 使用该 helper**

要求：
- 不再用 `expected_tokens = hf*wf` 截断 patch tokens（这会把 downscale 变成“左上角裁剪”）。
- 仍保留 sanity check：patch_tokens 的 token 数必须覆盖 `patch_h0*patch_w0`。
- `patch_h0/patch_w0` 从 `self.vggt_feat_input_size` 推导：
  - `patch_h0 = input_h // 14`
  - `patch_w0 = input_w // 14`
  - 并 assert `patch_h0*patch_w0 <= patch_tokens.shape[1]`

**Step 3: 运行 B1 测试应转 PASS**

Run:
```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_token_proj_resize_alignment.py
python3 scripts/tests/test_*.py
```
Expected: 全 PASS。

**Step 4: 提交**

Run:
```bash
git add third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py scripts/tests/test_token_proj_resize_alignment.py
git commit -m "fix(vggt): align token_proj phi render with cache downscale via bilinear resize"
```

---

### Task B3: 收敛 runner 默认值（降低 M1 灾难性退化概率）

**Files:**
- Modify: `scripts/run_train_feature_loss_v2_selfcap.sh`
- Modify: `docs/execution/2026-02-26-feature-loss-v2.md`

**Step 1: 调整 v2 runner 默认值（更保守）**

建议默认值（可按你判断微调，但必须有理由写在 commit message 或 doc）：
- `LAMBDA_VGGT_FEAT`：从 `0.05` 降到 `0.005` 或 `0.01`
- `VGGT_FEAT_RAMP_STEPS`：从 `200` 提到 `400`
- `TOKEN_LAYER_IDX`：从 `23` 改为 `17`（先保守提高成功率，匹配评审“stride16 中间层优先”的精神）
- 保持：`VGGT_FEAT_LOSS_TYPE=cosine`，`VGGT_FEAT_EVERY=8`

**Step 2: 更新执行文档的 M1 明确跑法（必须可比）**

在 `docs/execution/2026-02-26-feature-loss-v2.md` 的 Gate M1 段落补充一条硬要求：
- M1 的质量判定必须对齐 `baseline_smoke200`（同 step，同协议），不能用 `baseline_600` 直接对比 smoke200。

给出最短命令（文字即可，不要求实际跑）：
- baseline smoke200（建议用 env 覆盖 RESULT_DIR 落到 `outputs/protocol_v1/.../baseline_smoke200`）
- feature_loss_v2_smoke200
- feature_loss_v2_gated_smoke200

**Step 3: shell 语法检查 + 文档检查**

Run:
```bash
bash -n scripts/run_train_feature_loss_v2_selfcap.sh
python3 -m py_compile docs/execution/2026-02-26-feature-loss-v2.md || true
```
Expected: `bash -n` PASS（md 的 py_compile 可忽略）。

**Step 4: 提交**

Run:
```bash
git add scripts/run_train_feature_loss_v2_selfcap.sh docs/execution/2026-02-26-feature-loss-v2.md
git commit -m "docs+scripts: make v2 M1 defaults more conservative and require baseline_smoke200 comparison"
```

---

### Task B4: 推送 main + 同步 A 的“重新跑 M1”口径

**Files:**
- N/A

**Step 1: 最终测试**

Run:
```bash
python3 scripts/tests/test_*.py
bash -n scripts/run_train_feature_loss_v2_selfcap.sh
bash -n scripts/run_train_feature_loss_v2_gated_selfcap.sh
```
Expected: PASS。

**Step 2: push 到 main**

Run:
```bash
git push origin HEAD:main
```
Expected: push 成功。

**Step 3: 给 A 的一句话交接（复制粘贴）**

发给 A：
- 已修复 `token_proj` 与 cache `phi_downscale` 的对齐 bug（避免“左上角裁剪”错位）。
- 已把 v2 runner 默认参数改为更保守（lambda/ramp/layer）。
- 请 A 在 `origin/main` 上重新跑 M1：baseline_smoke200 + v2_smoke200 + v2_gated_smoke200；若 M1 PASS 再进 full600。

