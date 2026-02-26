# Feature-Loss 失败归因最小包（No-GPU）

## 目的与口径

- 目的：在不新增 full600 的前提下，形成可辩护的失败归因证据链，区分“实现级问题”与“方法假设边界/优化对抗”。
- 叙事纪律：Plan-B 的问题表述统一为 **velocity prior 的质量/尺度/一致性不足或噪声过大**，不使用“零速已被证实”等表述。
- 依据：`docs/reviews/2026-02-26/meeting-decision.md` 第 2.2 节的 5 项最小包。

## 1) Loss 量级曲线（photo vs feat）

目标：判断 `L_feat` 是否在后期主导并压制 photometric 分量。

命令：

```bash
python3 scripts/export_tb_scalars.py \
  --run_dir outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600 \
  --out_dir outputs/report_pack/diagnostics \
  --tags loss/total,loss/l1_raw,loss/feat_raw,loss_weighted/l1,loss_weighted/feat \
  --plot_png
```

产物：
- `outputs/report_pack/diagnostics/feature_loss_v2_postfix_600_tb_scalars.csv`
- `outputs/report_pack/diagnostics/feature_loss_v2_postfix_600_loss_curves.png`

## 2) Cache round-trip 一致性（phi(I_gt) offline vs online）

目标：排除缓存预处理/元数据不一致导致的伪退化。

命令：

```bash
python3 scripts/check_vggt_preprocess_consistency.py \
  --backend vggt \
  --data_dir data/selfcap/bar \
  --camera_ids 0,8,16,24,32,40,48,56 \
  --frame_start 0 \
  --num_frames 2 \
  --phi_name token_proj \
  --phi_downscale 4 \
  --dtype float16

python3 scripts/tests/test_vggt_cache_contract.py
python3 scripts/tests/test_token_proj_resize_alignment.py
```

判定：`self-consistency` 与 `cache round-trip` 均 PASS，且对齐单测通过。

## 3) 1–2px 平移敏感性（已补齐，phi-space 口径）

实现脚本：
- `scripts/analyze_phi_shift_sensitivity.py`

验证脚本：
- `scripts/tests/test_analyze_phi_shift_sensitivity.py`

执行命令（No-GPU）：

```bash
python3 scripts/analyze_phi_shift_sensitivity.py \
  --cache_npz /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260226-v2-postfix/outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
  --out_dir /root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics \
  --max_shift 2
```

证据路径（不入库）：
- `outputs/report_pack/diagnostics/phi_shift_sensitivity.csv`
- `outputs/report_pack/diagnostics/phi_shift_sensitivity.png`

说明：该项采用 **phi-space shift sensitivity**（对缓存 `phi` 做空间平移），用于证明“轻微错位会被特征损失放大”的趋势，不声称等价于 image-space shift。

## 4) Gating/Patch 命中率热图（已补齐）

实现脚本：
- `scripts/analyze_vggt_gate_framediff.py`

验证脚本：
- `scripts/tests/test_analyze_vggt_gate_framediff.py`

执行命令（No-GPU）：

```bash
python3 scripts/analyze_vggt_gate_framediff.py \
  --cache_npz /root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260226-v2-postfix/outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz \
  --out_dir /root/autodl-tmp/projects/4d-recon/outputs/report_pack/diagnostics
```

证据路径（不入库）：
- `outputs/report_pack/diagnostics/gate_framediff_mean_by_frame.csv`
- `outputs/report_pack/diagnostics/gate_framediff_mean_by_view.csv`
- `outputs/report_pack/diagnostics/gate_framediff_heatmap.png`

## 5) 梯度链检查（DONE）

目标：确认 feature loss 的梯度链路非零，避免“loss 有值但不驱动参数”。

证据路径：
- `outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv`
- `notes/feature_loss_v2_grad_chain_owner_a.md`
- `notes/handoff_feature_loss_v2_grad_chain_owner_a.md`

结论口径：
- 该检查用于排除“实现无效/梯度链断”的可能性；
- 即便梯度链路正常，也**不等价于**“feature-loss 方案可行”，后续仍需结合指标退化判定为优化对抗或方法边界。

## 建议收口顺序（10 分钟版）

1. 先跑第 1、2 项并固化 CSV/PNG 与 PASS 日志。
2. 第 3、4 项补一版最小统计图（可选）。
3. 第 5 项给出 10 step 梯度日志截图/CSV。
4. 在写作中统一口径：失败来自方法边界或优化对抗，而非“已证实的速度为零问题”。
