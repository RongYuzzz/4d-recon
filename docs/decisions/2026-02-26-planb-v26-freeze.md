# 2026-02-26 决议（v26）：Plan‑B 作为唯一主线，冻结训练并进入写作冲刺（新增 full600 预算 N=0）

日期：2026-02-26  
适用仓库：`/root/projects/4d-recon`  
上位/继承：`docs/decisions/2026-02-26-planb-pivot.md`（已执行并消耗当时 full600 预算）  
依据材料：
- `docs/reviews/2026-02-26/meeting-opinions-v26.md`
- `docs/reviews/2026-02-26/meeting-decisions-v26.md`
- `docs/reviews/2026-02-26/meeting-pack-v26.md`

## 1. 最终拍板（唯一主线）

1. 主线：**Plan‑B only**（不改 `protocol_v1`，仅替换 init velocities；其余协议、数据与训练口径不变）。
2. `feature-loss v2`：正式 **No‑Go 冻结**（作为负结果/边界条件与失败归因材料保留，不再作为主线推进）。
3. `Plan‑B + weak cue`：**No‑Go**（smoke200 证据不足，且 tLPIPS 未形成同向改善，不申请新增 full600）。

## 2. 算力预算与纪律（写死）

1. **新增 full600 预算：`N = 0`（默认不追加）。**
2. 冲刺期禁止新增训练：任何新增训练（含 full600/smoke200）必须先新建/升级决议文件，写清：
   - 动机（要回答什么问题）
   - 次数（N）、成功线、止损线
   - 对现有证据链的风险评估（避免“打散已锁定的 evidence pack”）
3. 允许的动作仅限 **No‑GPU/不改数值口径** 的补强与整理：
   - 重建 `report_pack`、重打 `evidence tar`、登记 `SHA256`
   - 补齐/统一 `stats/throughput.json`
   - 定性资产（side-by-side、抽帧）与写作素材整理
   - 失败归因最小包（plot/csv/说明文稿），不得改变训练逻辑

## 3. 会中数字引用口径（唯一真源）

会议/写作中引用任何数值时，**只允许**来自 v26 report-pack 快照：

- `docs/report_pack/2026-02-26-v26/metrics.csv`
- `docs/report_pack/2026-02-26-v26/scoreboard.md`
- `docs/report_pack/2026-02-26-v26/planb_anticherrypick.md`
- `docs/report_pack/2026-02-26-v26/manifest_sha256.csv`

离线证据包（不入库）：

- `artifacts/report_packs/report_pack_2026-02-26-v26.tar.gz`
- SHA 以 `artifacts/report_packs/SHA256SUMS.txt` 中登记为准

## 4. Scope 声明（避免“绝对 PSNR 原罪”攻击）

受限于算力预算，本阶段研究范围严格限定为：**稀疏视角 4DGS 在极短训练预算（600 steps）下的收敛行为与时序稳定性**。  
不声称最终高保真收敛上限（High-Fidelity at convergence），会议与写作应以“短预算下的可见改善 + 可审计证据链”为主。

## 5. Limitations（必须写进论文/答辩）

1. Feature Loss 与 Plan‑B 正交：Plan‑B 属于初始化策略，Feature Loss 属于训练期正则化；受限于预算，**未测试 Plan‑B + Feature Loss 组合**（写为未来工作而非漏洞）。
2. 负结果边界：在“劣质速度基底/短预算”设定下，`feature-loss v2` 的 full600 已表现为三项全劣化，故冻结主线并保留失败归因材料用于论证边界条件。

## 6. 未来 7 天交付物（写作优先，避免发散）

1. 一页式结论页：baseline vs Plan‑B vs feature-loss（canonical + seg 防守要点 + 一句 scope）。
2. 主表（Table 1）：canonical full600 + seg200_260 full600（含 Δ 与指标定义）。
3. anti-cherrypick 附录：多切片 smoke200 同向证据 + template hygiene 声明。
4. 定性对比清单：canonical/seg200_260/seg 片段 side-by-side 播放顺序与抽帧图。
5. Q&A 防守卡片：针对“cherry-pick/投机速度/绝对 PSNR/为何不做组合”等问题给出一致话术。

