# Owner A 后续计划：Writing Mode（v26 冻结期）生成可播放 loop clip + 会议 Runbook（不新增训练）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0 可用但本计划默认不使用 GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

现有 side-by-side 视频普遍时长较短（~1.667s），会上容易“来不及看清”。本计划在 **不新增训练** 前提下：

1. 生成 **可循环播放** 的 `loop12s` 版本（PPT/Keynote 更稳、更易讲解）。
2. 生成每个 clip 的 **静态封面图**（播放器出问题时的兜底）。
3. 产出一份 **会议播放 Runbook**（一键自检 + 播放命令 + 兜底路径），并入库 notes。

## 1) 约束（必须遵守）

- 禁止新增训练：不运行任何 `run_train_*.sh`，不新增 smoke200/full600。
- 不改 `docs/protocols/protocol_v1.yaml` 与训练数值逻辑。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 允许入库：`notes/*`（本计划默认不改脚本/测试）。

## 2) 输入（应已存在；若缺失则记录缺口，不补训练）

源视频（任选其一为输入即可；优先级从高到低）：

- canonical：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4`
- seg200_260：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4`
- seg400_460：`outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4`

若已存在 A152 产物，也可直接用 `_12s_h264.mp4` 作为输入再 loop：

- `outputs/qualitative/planb_vs_baseline/clips_v26/*_12s_h264.mp4`

## 3) 任务分解（A161–A164）

### A161. 生成 loop12s 可嵌入版本（No‑GPU）

输出目录（不入库）：

- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/`

命令（对 3 个源视频各生成 1 个 loop12s h264 文件）：

```bash
cd /root/projects/4d-recon
OUT=outputs/qualitative/planb_vs_baseline/clips_v26_looped
mkdir -p "$OUT"

loop12s() {
  in="$1"
  base="$(basename "$in" .mp4)"
  ffmpeg -hide_banner -loglevel error -y \
    -stream_loop -1 -i "$in" -t 12 \
    -vf "scale=1280:-2" \
    -an -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
    "$OUT/${base}_loop12s_h264.mp4"
}

loop12s outputs/qualitative/planb_vs_baseline/planb_vs_baseline_step599.mp4
loop12s outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg200_260_step599.mp4
loop12s outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg400_460_step199.mp4
```

验收：

- `ffprobe` 显示每个新文件 `duration` 约 12s，分辨率约 `1280x*`：
```bash
for p in outputs/qualitative/planb_vs_baseline/clips_v26_looped/*_loop12s_h264.mp4; do
  ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of default=nw=1 "$p"
done
```

### A162. 生成每个 loop clip 的封面图（No‑GPU）

输出目录（不入库）：

- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`

命令（取 6 秒处 1 帧）：

```bash
cd /root/projects/4d-recon
OUT=outputs/qualitative/planb_vs_baseline/clips_v26_looped
mkdir -p "$OUT/covers"

for mp4 in "$OUT"/*_loop12s_h264.mp4; do
  base="$(basename "$mp4" .mp4)"
  ffmpeg -hide_banner -loglevel error -y -ss 6 -i "$mp4" -frames:v 1 "$OUT/covers/${base}_t6.jpg"
done
```

验收：`covers/` 下每个 clip 至少 1 张 jpg，且 `file`/`ffprobe` 可读。

### A163. 会议播放 Runbook（入库 notes）

新增（入库）：

- `notes/planb_meeting_runbook_v26_owner_a.md`

必须包含：

- 会前 30 秒自检（`ffprobe` 三个 loop clip + 原始 mp4 存在性）。
- 播放命令（优先 `ffplay`；若你习惯 `mpv` 可附备用）：
  - canonical → seg200_260 → seg400_460 的推荐顺序
- 兜底路径：
  - 若视频播放失败：使用 `covers/*.jpg` 做 freeze-frame 对比
  - 若 loop clip 缺失：退回播放原始 mp4（在 notes 明确路径）

### A164. 入库提交（只提交 1 个 notes 文件）

```bash
cd /root/projects/4d-recon
git add notes/planb_meeting_runbook_v26_owner_a.md
git commit -m "docs(planb): add v26 meeting playback runbook (owner-a)"
git push origin HEAD:main
```

验收：commit 仅包含该 notes；不包含 `outputs/`、`data/`、`*.tar.gz`。

## 4) 交接给 Owner B（并行点）

当 A161/A162 完成后，给 B 一句话 unblock：

- loop clip 目录：`outputs/qualitative/planb_vs_baseline/clips_v26_looped/`
- covers 目录：`outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers/`
- 入库 runbook：`notes/planb_meeting_runbook_v26_owner_a.md`

B 可以选择性在 `meeting-handout-v26.md` 或 `planb_onepager_v26.md` 追加一行“loop clip 优先播放”的提示（不需要新 report-pack）。

