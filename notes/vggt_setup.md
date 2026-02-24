# VGGT Setup Notes (Operational Backend)

截至 `2026-02-24`，`scripts/cue_mining.py --backend vggt` 已可直接运行并产出：
- `pseudo_masks.npz`
- `quality.json`
- `viz/overlay_cam02_frame000000.jpg`
- `viz/grid_frame000000.jpg`

## 1) 依赖与版本

- Python 环境：`/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv`
- 安装方式：

```bash
source /etc/network_turbo
/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/pip install \
  'git+https://github.com/facebookresearch/vggt.git'
```

- VGGT pip 源信息（`direct_url.json`）：
  - repo: `https://github.com/facebookresearch/vggt.git`
  - commit: `44b3afbd1869d8bde4894dd8ea1e293112dd5eba`
- HF 模型：
  - model id: `facebook/VGGT-1B`
  - 本机快照：`860abec7937da0a4c03c41d3c269c366e82abdf9`

## 2) 权重下载

```bash
source /etc/network_turbo
export HF_HUB_DISABLE_XET=1
/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
print(snapshot_download("facebook/VGGT-1B"))
PY
```

说明：
- 当前网络环境推荐 `HF_HUB_DISABLE_XET=1`，避免 Xet 401。
- 下载支持断点续传，可重复执行。

## 3) 运行命令（已验收）

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
export HF_HUB_OFFLINE=1
export HF_HUB_DISABLE_XET=1
BASE_DIR=/root/projects/4d-recon/third_party/FreeTimeGsVanilla \
GPU=0 OUT_DIR=outputs/cue_mining/selfcap_bar_8cam60f_vggt_smoke \
bash scripts/run_cue_mining.sh /root/autodl-tmp/projects/4d-recon/data/selfcap_bar_8cam60f \
  selfcap_bar_8cam60f_vggt_smoke 0 2 vggt 4
```

```bash
cd /root/projects/4d-recon/.worktrees/owner-a-20260224-cuev2-seg2
export HF_HUB_OFFLINE=1
export HF_HUB_DISABLE_XET=1
BASE_DIR=/root/projects/4d-recon/third_party/FreeTimeGsVanilla \
GPU=0 OUT_DIR=outputs/cue_mining/selfcap_bar_8cam60f_vggt_full60 \
bash scripts/run_cue_mining.sh /root/autodl-tmp/projects/4d-recon/data/selfcap_bar_8cam60f \
  selfcap_bar_8cam60f_vggt_full60 0 60 vggt 4
```

实际耗时（full 60 帧，一次实测）：
- `real 0m52.932s`
- `user 12m19.171s`
- `sys 0m21.113s`

## 4) 错误处理约定（无 silent fallback）

- `--backend vggt` 出错时脚本立即失败，不会自动回退到 `diff`。
- 典型失败提示：
  - 缺依赖：提示 `pip install 'git+https://github.com/facebookresearch/vggt.git'`
  - 权重不可加载：提示模型 id/cache 的具体错误

## 5) 当前验收产物

- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_smoke/pseudo_masks.npz`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_smoke/quality.json`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_full60/pseudo_masks.npz`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_full60/quality.json`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_full60/viz/overlay_cam02_frame000000.jpg`
- `outputs/cue_mining/selfcap_bar_8cam60f_vggt_full60/viz/grid_frame000000.jpg`
