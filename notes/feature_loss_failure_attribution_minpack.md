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

## 3) 1–2px 平移敏感性（可选加分项）

当前状态：仓库暂无独立脚本，建议作为无训练开销的附加诊断。

最小实现思路：
- 取同一帧 GT 图像 `I_gt`，构造 `(dx,dy) ∈ {(-2,-2)...(2,2)}` 的平移版本；
- 通过与 cache 同一 `phi` 提取路径计算 `L_feat(shift(I_gt), I_gt)`；
- 输出 `shift -> loss` 曲线，观察 1px 级别是否出现异常陡增。

## 4) Gating/Patch 命中率热图（待补/可选）

当前状态：仓库暂无专用可视化脚本；可使用已存在数据源先完成统计版。

数据源：
- `scripts/precompute_vggt_cache.py --save_framediff_gate` 会把 `gate_framediff` 写入 `gt_cache.npz`。

最小统计口径：
- 统计每帧/每视角 gate 激活比例（mean of `gate_framediff`）；
- 对 60 帧输出时序曲线，并抽样导出 2D 热图 PNG。

## 5) 梯度链检查（10 step 小跑）

目标：确认 feature loss 的梯度链路非零，避免“loss 有值但不驱动参数”。

建议执行：
- 在 10 step 小跑中打印/记录 `||grad(render_rgb)||` 与 `||grad(gaussian params)||`；
- 可沿用 trainer 现有 grad 日志路径机制（例如 `t0_grad_log_path`）并增加 feature-loss 相关 norm 打印；
- 本任务不改训练数值逻辑，只做日志/诊断补丁。

判定：
- 若梯度接近 0：优先归类为实现链路问题；
- 若梯度正常但指标仍退化：归类为优化对抗或方法边界。

## 建议收口顺序（10 分钟版）

1. 先跑第 1、2 项并固化 CSV/PNG 与 PASS 日志。
2. 第 3、4 项补一版最小统计图（可选）。
3. 第 5 项给出 10 step 梯度日志截图/CSV。
4. 在写作中统一口径：失败来自方法边界或优化对抗，而非“已证实的速度为零问题”。
