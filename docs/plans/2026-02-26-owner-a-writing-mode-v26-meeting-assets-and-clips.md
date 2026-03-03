# Owner A 后续计划：Writing Mode（v26 冻结期）会议定性资产裁剪与清单化（不新增训练）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0 可用但本计划默认不使用 GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

把现有 side-by-side 定性视频整理成“会上可秒开、可嵌 slide、可分发”的资产包（不入库大文件），并产出可审计的清单与引用入口（入库 notes）。

## 1) 约束（必须遵守）

- 禁止新增训练：不运行任何 `run_train_*.sh`，不新增任何 smoke200/full600。
- 不改 `docs/protocols/protocol_v1.yaml` 与训练数值逻辑。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 允许入库：`notes/*`（本计划默认不改脚本/测试）。

## 2) 输入（应已存在，若缺失则记录缺口，不补训练）

主视频（优先级从高到低）：

1. `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`（canonical full600）
2. `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`（seg200_260 full600）
3. `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`（smoke200 示例；可替换为 seg300/600/1800 任一）

## 3) 任务分解（A151–A154）

### A151. 会前播放自检（No‑GPU，5 分钟）

```bash
cd /root/projects/4d-recon
for p in \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4 \
; do
  test -f "$p" && ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$p"
done
```

验收：

- 三个文件存在且 `ffprobe` 可读到 `duration/size`。
- 若缺失任一文件：在 notes 中记录缺口并给出可用替代文件路径（不补训练）。

### A152. 裁剪会议短片（No‑GPU）

目的：生成短片（建议 8–12 秒）以便嵌入 PPT/Keynote，避免原视频过大或开场缓冲。

输出目录（不入库）：

- `outputs/qualitative/planb_vs_baseline/clips_v26/`

命令模板（对每个 mp4 生成 2 个版本：原码率 copy 裁剪 + 低码率可嵌入版）：

```bash
cd /root/projects/4d-recon
OUT=outputs/qualitative/planb_vs_baseline/clips_v26
mkdir -p "$OUT"

clip() {
  in="$1"
  base="$(basename "$in" .mp4)"
  # 版本1：无重编码（快，但可能不兼容所有播放器）
  ffmpeg -hide_banner -loglevel error -y -ss 0 -t 12 -i "$in" -c copy "$OUT/${base}_12s_copy.mp4"
  # 版本2：重编码（更稳，适合 PPT）
  ffmpeg -hide_banner -loglevel error -y -ss 0 -t 12 -i "$in" \
    -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -c:a aac -b:a 128k \
    "$OUT/${base}_12s_h264.mp4"
}

clip outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4
clip outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4
clip outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4
```

验收：

- `clips_v26/` 下每个源视频至少生成 2 个 clip；
- `ffprobe` 能读取新 clip 的时长与分辨率；
- 单个 clip 建议 < 30MB（若超出，在 notes 记录并调高 `-crf` 或降 `scale`）。

### A153. 抽帧“主图组”统一落位（No‑GPU）

目的：生成可直接贴 slide 的 jpg，并确保命名不冲突、便于引用。

输出目录（不入库）：

- `outputs/qualitative/planb_vs_baseline/frames_selected_v26/`

```bash
cd /root/projects/4d-recon
OUT=outputs/qualitative/planb_vs_baseline/frames_selected_v26
mkdir -p "$OUT"

extract3() {
  in="$1"
  base="$(basename "$in" .mp4)"
  bash scripts/extract_video_frames.sh "$in" "$OUT/frame_${base}_000000.jpg" 0
  bash scripts/extract_video_frames.sh "$in" "$OUT/frame_${base}_000030.jpg" 30
  bash scripts/extract_video_frames.sh "$in" "$OUT/frame_${base}_000059.jpg" 59
}

extract3 outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4
extract3 outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4
extract3 outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4
```

验收：

- 每个视频产出 3 张 jpg（共 9 张）；
- 文件名包含 `segXXX_YYY` 与 `step` 信息（通过 `base` 体现）。

### A154. 入库清单与 handoff（只提交 notes）

新增（入库）：

- `notes/planb_meeting_assets_v26_owner_a.md`

内容必须包含：

- 源视频清单（3 个）与用途（canonical/seg200_260/示例 seg）。
- `clips_v26/` 下生成的 clip 清单（含大小、时长；建议贴 `ffprobe` 摘录）。
- `frames_selected_v26/` 下推荐主图组（每个视频 3 帧）清单。
- 会议播放顺序建议（<=5 分钟播完）。
- 提醒：本计划不产生任何新增训练，不改变任何指标口径。

提交规范（主仓或 worktree 均可）：

```bash
cd /root/projects/4d-recon
git add notes/planb_meeting_assets_v26_owner_a.md
git commit -m "docs(planb): add v26 meeting qualitative clips/frames manifest (owner-a)"
git push origin HEAD:main
```

验收：

- `origin/main` 可见新增 notes；
- commit 只包含该 notes 文件。

