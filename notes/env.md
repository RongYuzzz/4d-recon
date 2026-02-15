# Environment Notes

## Host Snapshot
- Date (UTC): `2026-02-15T03:57:09Z`
- Python: `3.12.3` (`/root/miniconda3/bin/python3`)
- GPU: `NVIDIA GeForce RTX 5090` (`32607 MiB`)
- Driver: `580.76.05`

## Workspace
- Project root: `/root/projects/4d-recon`
- Third-party base: `/root/projects/4d-recon/third_party/FreeTimeGsVanilla`

## Virtual Environment
```bash
cd /root/projects/4d-recon/third_party/FreeTimeGsVanilla
python3 -m venv .venv
source .venv/bin/activate
python --version
pip --version
```

## Dependency Installation Status
### Attempt 1
```bash
pip install -e .
```
- 结果：失败。
- 失败点：`torch_scatter` 在构建依赖阶段报错 `ModuleNotFoundError: No module named 'torch'`。
- 结论：需要分步安装，先安装 `torch` 再安装其余包。

### Attempt 2 (success)
```bash
source .venv/bin/activate
pip install torch torchvision
pip install pycolmap viser nerfview 'imageio[ffmpeg]' numpy==1.26.4 scikit-learn tqdm \
  'torchmetrics[image]<1.5' opencv-python tyro pillow tensorboard tensorly pyyaml \
  matplotlib natsort plotly open3d
pip install gsplat
pip install --no-build-isolation https://codeload.github.com/rahul-goel/fused-ssim/tar.gz/1272e21a282342e89537159e4bad508b19b34157
pip install --no-build-isolation https://codeload.github.com/fraunhoferhhi/PLAS/tar.gz/main
pip install --no-build-isolation torch-scatter -f https://data.pyg.org/whl/torch-2.10.0+cu128.html
pip install splines
pip install -e . --no-build-isolation
```
- 结果：成功，`freetimegs` 已可编辑安装。
- 说明：`fused-ssim` 和 `PLAS` 通过 `codeload.github.com` tarball 安装（绕过 `git clone` 限制）。
- 关键：`torch-scatter` 需要 `--no-build-isolation`，并在本机编译 CUDA 扩展。

### Import Check
已验证以下模块可导入：
- `torch`, `torchvision`, `pycolmap`, `viser`, `nerfview`, `opencv-python`
- `torchmetrics`, `tensorboard`, `tensorly`, `matplotlib`, `open3d`
- `torch_scatter`, `fused_ssim`, `plas`, `gsplat`

## Minimal Data Requirement (Task 2)
训练最小闭环至少需要：
- Triangulation keyframe 输入目录：`points3d_frameXXXXXX.npy` + `colors_frameXXXXXX.npy`
- COLMAP 目录：
  - `images/`
  - `sparse/0/cameras.bin`
  - `sparse/0/images.bin`
  - `sparse/0/points3D.bin`

建议将单场景数据放到：
- `/root/projects/4d-recon/data/<scene>/triangulation/`
- `/root/projects/4d-recon/data/<scene>/colmap/`
