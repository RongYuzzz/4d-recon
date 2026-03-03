# protocol_v2 Post Dual-GPU Smoke Next Tasks (Owner A / GPU0)

日期：2026-02-28  
前置结论：dual‑GPU smoke200 未找到稳定候选（未满足“≥2 seeds 同时 ΔtLPIPS<=0 且 ΔLPIPS<=0 且幅度显著大于噪声带”），因此**不触发新增 full600 预算讨论**，stage‑2 继续按 `mixed trend + failure analysis` 收口。

本文件仅列 Owner A 的后续任务（可与 Owner B 并行）。

---

## 不变量 / 纪律（必须遵守）

1. 不新增 full600（除非形成新的预算决议文件）。
2. 任何新增训练仅允许 smoke200，且必须显式写 `GPU=0 MAX_STEPS=200`。
3. 所有新产物仅写入 `outputs/protocol_v2/...`，不覆盖既有 stage‑1/v26 证据链。

---

## Task A1（必须）：修正审计口径，标注“feature loss 未生效”的 runs

**动机**：避免把“未启用 feature loss”的 runs 误判为 feature‑loss 结论。

**要做什么**：
- 在 `notes/protocol_v2_planb_feat_smoke200_owner_a.md` 的 A2/A3 小节补 2 行说明：
  - 当 `MAX_STEPS=200` 且 `VGGT_FEAT_START_STEP=200` 时，训练循环最后 `step=199`，满足不了 `step >= start_step`，因此 **feature loss 实际不生效**；
  - A2/A3 仅作为“噪声/随机性参考”，不纳入“feature‑loss 超参对比”的结论。

**Done**：note 已补充上述说明，并在 handoff/收口结论里同步该解释。

---

## Task A2（必须）：给训练入口加防呆（避免再次烧 GPU 跑出“无效对照”）

**动机**：dual‑GPU sweep 已暴露一个高频踩坑：`start_step >= max_steps` 会导致“看似开了 feature loss，实际完全没启用”。

**要做什么（两条即可，保持轻量）**：
1) 修改 `scripts/run_train_planb_feature_loss_v2_selfcap.sh`：  
   - 若 `LAMBDA_VGGT_FEAT>0` 且 `VGGT_FEAT_START_STEP>=MAX_STEPS` → 直接 `exit 1`，提示“feature loss will never run（请调小 start_step 或增大 max_steps）”。
2) framediff gating 警告（不改行为，只警告）：  
   - 若 `VGGT_FEAT_GATING=framediff` 且 `VGGT_FEAT_GATING_TOP_P` 与 cache `meta.json:framediff_top_p` 不一致 → 打印 WARN，提示“若要严格比较不同 top‑p，应生成新 cache（不同 framediff_top_p）”。

**Done**：脚本具备上述防呆；并新增/更新 1 个最小单测（例如在 `scripts/tests/` 下检查脚本包含该 guard 文本即可）。

---

## Task A3（可选，timebox 2h）：framediff gate 可视化（用于失败分析与答辩解释）

**动机**：我们已经引入 framediff gate，但当前只有数值结论；补一页“gate 在看什么”的图，有助于解释为什么它不一定改善 tLPIPS。

**要做什么**：
- 从 framediff cache 导出 2–3 帧 × 1–2 视角的 gate overlay（p=0.10 vs p=0.02 对比即可）：
  - 旧 cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4/gt_cache.npz`
  - 新 cache：`outputs/vggt_cache/selfcap_bar_8cam60f_token_proj_l17_d32_s20260225_f0_n60_cam8_ds4_fdtop002/gt_cache.npz`
- 输出到 `outputs/vggt_cache/.../viz_gate/`（或新建 `outputs/viz/gate_framediff/`），并写一个短 note 指针（新建 `notes/protocol_v2_framediff_gate_viz.md` 亦可）。

**Done**：有可引用的 overlay 图 + 一句话结论（gate 主要覆盖哪些区域/失败边界）。

