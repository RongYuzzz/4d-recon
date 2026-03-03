# Owner A 后续计划：Writing Mode（v26 冻结期）扩展 loop clips + 离线 bundle（不新增训练）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0 可用但本计划默认不使用 GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

在不新增训练前提下，把定性证据进一步做成“可扩展、可分发、可兜底”的会议资产：

1. 为更多 anti-cherrypick 切片生成 `loop12s` 版本（可循环播放，便于讲清细节）。
2. 生成对应 covers（freeze-frame 兜底）。
3. 打一份**离线 bundle tar**（本地，不入库），便于发给导师/同行或跨机器拷贝。
4. 更新现有会议资产清单 notes（只改 docs/notes，不入库 outputs）。

## 1) 约束（必须遵守）

- 禁止新增训练：不运行任何 `run_train_*.sh`，不新增 smoke200/full600。
- 不改 `docs/protocols/protocol_v1.yaml` 与训练数值逻辑。
- `data/`、`outputs/`、`artifacts/report_packs/*.tar.gz` 不入库。
- 允许入库：`notes/*`（本计划默认仅更新 1 个 notes 文件）。

## 2) 输入（应已存在；若缺失则记录缺口，不补训练）

已具备 loop clip（A161 已做）：

- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_step599_loop12s_h264.mp4`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg200_260_step599_loop12s_h264.mp4`
- `outputs/qualitative/planb_vs_baseline/clips_v26_looped/planb_vs_baseline_seg400_460_step199_loop12s_h264.mp4`

可选扩展（若源 mp4 存在则生成 loop clip）：

- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4`
- `outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4`

## 3) 任务分解（A171–A175）

### A171. 资产存在性与播放器自检（No‑GPU，2 分钟）

```bash
cd /root/projects/4d-recon
command -v ffmpeg
command -v ffprobe
command -v ffplay || true
command -v mpv || true

for p in \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4 \
; do
  test -f "$p" && echo "[OK] $p" || echo "[MISS] $p"
done
```

验收：记录哪些源视频存在/缺失（缺失不阻塞后续）。

### A172. 生成额外切片 loop12s clips + covers（No‑GPU）

```bash
cd /root/projects/4d-recon
OUT=outputs/qualitative/planb_vs_baseline/clips_v26_looped
mkdir -p "$OUT" "$OUT/covers"

loop12s() {
  in="$1"
  base="$(basename "$in" .mp4)"
  ffmpeg -hide_banner -loglevel error -y \
    -stream_loop -1 -i "$in" -t 12 \
    -vf "scale=1280:-2" -an \
    -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
    "$OUT/${base}_loop12s_h264.mp4"
  ffmpeg -hide_banner -loglevel error -y -ss 6 -i "$OUT/${base}_loop12s_h264.mp4" -frames:v 1 \
    "$OUT/covers/${base}_loop12s_h264_t6.jpg"
}

for p in \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg300_360_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg600_660_step199.mp4 \
  outputs/qualitative/planb_vs_baseline/planb_vs_baseline_seg1800_1860_step199.mp4 \
; do
  test -f "$p" && loop12s "$p"
done

# probe 新生成的 clips（存在才 probe）
for p in "$OUT"/*_seg300_360_*_loop12s_h264.mp4 "$OUT"/*_seg600_660_*_loop12s_h264.mp4 "$OUT"/*_seg1800_1860_*_loop12s_h264.mp4; do
  test -f "$p" && ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of default=nw=1 "$p"
done
```

验收：

- 新生成 clip 的 `duration` 为 ~12s，分辨率为 `1280x*`。
- covers 图片可 `file` 读取且与 clip 分辨率一致。

### A173. 打离线 bundle tar（本地，不入库）

目的：方便跨机器拷贝/发给导师（避免临场找文件）。

输出（不入库）：

- `artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`

```bash
cd /root/projects/4d-recon
mkdir -p artifacts/meeting_assets

tar -czf artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz \
  docs/reviews/2026-02-26/meeting-index-v26.md \
  docs/reviews/2026-02-26/meeting-handout-v26.md \
  docs/writing/planb_onepager_v26.md \
  docs/writing/planb_talk_outline_v26.md \
  docs/writing/planb_qa_cards_v26.md \
  notes/planb_meeting_assets_v26_owner_a.md \
  notes/planb_meeting_runbook_v26_owner_a.md \
  outputs/qualitative/planb_vs_baseline/clips_v26_looped \
  outputs/qualitative/planb_vs_baseline/frames_selected_v26 \
  outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers

sha256sum artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz
```

验收：tar 可解压；sha256 记录到 notes（见下一步）。

### A174. 更新会议资产清单 notes（入库，仅改 1 个文件）

Modify（入库）：

- `notes/planb_meeting_assets_v26_owner_a.md`

追加两段即可（最小增量）：

1. **Optional slices**：列出若 A172 成功生成的 seg300/seg600/seg1800 loop clip 文件名与用途（用于 anti-cherrypick 追问时现场补刀）。
2. **Offline bundle**：记录 `artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz` 的 `sha256sum` 输出与验证命令。

### A175. 入库提交（只提交该 notes 文件）

```bash
cd /root/projects/4d-recon
git add notes/planb_meeting_assets_v26_owner_a.md
git commit -m "docs(planb): extend v26 meeting assets manifest with looped clips + offline bundle"
git push origin HEAD:main
```

验收：commit 仅包含该 notes 文件；不包含任何 `outputs/`、`data/`、`*.tar.gz` 入库。

