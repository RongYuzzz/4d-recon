# VGGT Setup Notes (Optional Backend)

当前 `scripts/cue_mining.py --backend vggt` 仅保留接口，默认不会自动下载权重。

## 当前建议

- 先使用 `--backend diff` 跑通 MVP（本仓默认路径）。
- 若要启用 `vggt`：
  - 准备 VGGT 推理代码与权重目录；
  - 在本仓中补充加载逻辑（输入多视角帧，输出每视角 pseudo mask）；
  - 保持 `pseudo_masks.npz` 契约不变（见 `notes/cue_mining_spec.md`）。

## 错误处理约定

- 当 `--backend vggt` 但依赖/权重缺失时，脚本应立即报错并退出；
- 错误信息需包含下一步指引：回退 `--backend diff` 或补齐 VGGT 环境。
