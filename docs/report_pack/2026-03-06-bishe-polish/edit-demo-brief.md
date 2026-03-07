# Edit Demo Brief

## What is shown

当前交付的是“基于动静分层导出的可编辑演示雏形”：它已经能够展示 dynamic/static 分离与 removal-style filtering 的可视效果，但仍不是完整的 object inpainting/editing system。

这里的核心证据不是“做出了一个完整编辑器”，而是已经在现有 4DGS 管线中把 `dynamic/static` 两层显式导出，并能用 `static-only` / `dynamic-only` 的视频与抽帧结果说明：当前系统确实学到了一定程度的动静解耦表征。对毕设口径而言，这是一份“可编辑性证据包”，不是“完整产品功能”。

## Why this aligns with the original proposal

原版开题 `4D-Reconstruction.md` 的第三条主线，强调的是“基于动静解耦机制的 4D 重建框架构建与验证”，并要求通过“场景解耦与编辑（如物体移除）”做定性验证。当前这份 demo 与该目标的对齐点在于：

- 它已经给出 `动静解耦` 的直接可视证据，而不是只停留在数值指标；
- 它已经能通过 `static-only` 导出展示 removal-style 结果，支撑“物体移除”方向的最小闭环；
- 它与 `notes/protocol_v2_static_dynamic_tau.md` 中的阈值选择、与 `notes/openproposal_phase5_edit_demo.md` 中的失败边界口径保持一致，属于同一条“可编辑性/解释性”证据链。

## What the demo is and is not

- **It is:** dynamic/static filtering-based editable evidence，用来证明当前表征具备一定的分层与 removal-style 操控能力。
- **It is not:** a full object editing pipeline；更不是完整的可交互内容生成系统。
- **Guardrail:** this is filtering, `not inpainting`。被移除的动态层如果原本遮挡了背景、或背景本来就没有被充分观测，那么导出后会出现 holes / ghosting / 背景缺失。
- 这与 `notes/openproposal_phase5_edit_demo.md` 中已经明确记录的限制一致：当前 removal demo 的本质是 filtering，而不是补全被遮挡区域的 object inpainting。

## Deliverable paths

主视频证据：

- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_static_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/protocol_v2/selfcap_bar_8cam60f/export_planb_dynamic_tau0.075436/videos/traj_4d_step599.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`

补充说明：

- 阈值选择与已知泄漏模式：`notes/protocol_v2_static_dynamic_tau.md`
- 与 removal demo 同口径的边界说明：`notes/openproposal_phase5_edit_demo.md`
- 本次答辩/汇报用抽帧包：`outputs/qualitative_local/bishe_edit_demo_frames/`

## Failure boundary

这份 demo 的失败边界必须明确写清：

- 慢速运动体可能泄漏进 `static-only`，因此“物体移除”不是严格的实例级 clean removal；
- 抖动背景或边缘噪声可能泄漏进 `dynamic-only`；
- 若被移除的动态区域后方本身缺少观测，导出结果会出现 holes / ghosting，这进一步说明当前交付是 filtering-based evidence，而不是补全式编辑系统；
- 因此，这份材料最适合支撑“动静解耦 + removal-style 物体移除的定性证据”，不适合包装成“完整 object editing / inpainting 系统已完成”。
