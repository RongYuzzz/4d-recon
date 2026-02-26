# Handoff: feature_loss_v2 grad-chain + postfix_600 expose（Owner A -> Owner B）

- Date: 2026-02-26
- Repo: `/root/projects/4d-recon`

## 1) `feature_loss_v2_postfix_600` 暴露路径（主阵地可见）

已按计划用 symlink 暴露到主阵地：

- 暴露路径（DST）  
  `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600`
- 链接目标（SRC）  
  `/root/autodl-tmp/projects/4d-recon/.worktrees/owner-a-20260226-v2-postfix/outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600`

已验收可读关键文件：
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/stats/test_step0599.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/stats/val_step0599.json`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/videos/traj_4d_step599.mp4`
- `outputs/protocol_v1/selfcap_bar_8cam60f/feature_loss_v2_postfix_600/tb/events.out.tfevents*`

## 2) 梯度链证据（可被 evidence 自动收录）

- CSV 路径：  
  `outputs/report_pack/diagnostics/feature_loss_v2_grad_chain.csv`
- 内容结论：step 0~9 的 `vel_grad_norm` / `duration_grad_norm` 均非 0，且 `*_finite` 全为 1。

## 3) Owner B（v21 打包）无 GPU 使用方式

Owner B 无需重跑训练，直接在主仓执行现有打包流程即可自动带上该 CSV：

```bash
cd /root/projects/4d-recon
python3 scripts/build_report_pack.py
python3 scripts/pack_evidence.py
```

`pack_evidence.py` 会递归收录 `outputs/report_pack/**`，因此上述梯度 CSV 会随 evidence 包一起进入交付链。
