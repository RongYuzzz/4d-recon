# Owner A 后续计划：Writing Mode（v26 冻结期）离线 bundle 卫生 + 可搬迁自检（不新增训练）

日期：2026-02-26  
主阵地：`/root/projects/4d-recon`  
执行人：Owner A（GPU0 可用但本计划默认不使用 GPU）  
唯一决议真源：`docs/decisions/2026-02-26-planb-v26-freeze.md`（新增 full600 预算 `N=0`，禁止新增训练）

## 0) 目标

你们已经生成了会议离线包 `artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz`（不入库）。本计划做两件“防翻车”工作：

1. 避免离线包在主仓里持续以 untracked 形式污染 `git status` 或被误入库（gitignore 卫生）。
2. 做一次“可搬迁自检”：解包到临时目录后，确认会议入口页/播放 runbook/视频资产都可在**无仓库环境**下打开与引用（至少路径存在）。

## 1) 约束（必须遵守）

- 禁止新增训练：不运行任何 `run_train_*.sh`，不新增 smoke200/full600。
- 不改 `docs/protocols/protocol_v1.yaml` 与训练数值逻辑。
- `data/`、`outputs/`、`artifacts/*/*.tar.gz` 不入库（本计划只允许提交 `.gitignore` 与 1 个 notes）。

## 2) 任务分解（A181–A184）

### A181. `.gitignore` 增补（防误入库 + 清爽 status）

修改（入库）：

- `.gitignore`

在 “Local artifacts” 相关段落下追加一行即可（最小增量）：

```gitignore
artifacts/meeting_assets/*.tar.gz
```

验收：

- `git status` 不再出现 `?? artifacts/meeting_assets/`。
- 不影响现有 `artifacts/report_packs/*.tar.gz` 规则。

### A182. 离线 bundle 可搬迁自检（No‑GPU，10 分钟）

Run：
```bash
cd /root/projects/4d-recon

TAR=artifacts/meeting_assets/planb_meeting_assets_v26.tar.gz
test -f "$TAR"
sha256sum "$TAR"

TMP="$(mktemp -d)"
tar -xzf "$TAR" -C "$TMP"

# 关键入口文件存在性（相对路径在解包目录下应可找到）
for p in \
  docs/reviews/2026-02-26/meeting-index-v26.md \
  docs/reviews/2026-02-26/meeting-handout-v26.md \
  docs/reviews/2026-02-26/meeting-checklist-v26.md \
  docs/writing/planb_onepager_v26.md \
  docs/writing/planb_talk_outline_v26.md \
  docs/writing/planb_qa_cards_v26.md \
  notes/planb_meeting_assets_v26_owner_a.md \
  notes/planb_meeting_runbook_v26_owner_a.md \
; do
  test -f "$TMP/$p" && echo "[OK] $p" || echo "[MISS] $p"
done

# loop clips / covers 目录存在性
test -d "$TMP/outputs/qualitative/planb_vs_baseline/clips_v26_looped" && echo "[OK] looped clips dir"
test -d "$TMP/outputs/qualitative/planb_vs_baseline/clips_v26_looped/covers" && echo "[OK] covers dir"
```

验收：

- 上述 `for p in ...` 全部 `[OK]`。
- loop clips 与 covers 目录均存在。

### A183. 记录自检结果（入库 notes）

新增（入库）：

- `notes/meeting_offline_bundle_v26_selfcheck_owner_a.md`

内容最少包含：

- bundle 路径 + `sha256sum` 输出（与 `notes/planb_meeting_assets_v26_owner_a.md` 中一致）。
- A182 的关键 `[OK]` 列表（不用贴长输出，列出缺失项即可；若全 OK 写 “PASS”）。
- 一句提醒：bundle 为本地离线物料，不入库。

### A184. 收尾提交（只提交 `.gitignore` + 1 个 notes）

```bash
cd /root/projects/4d-recon
python3 scripts/tests/test_build_report_pack.py
python3 scripts/tests/test_summarize_scoreboard.py
python3 scripts/tests/test_summarize_planb_anticherrypick.py

git add .gitignore notes/meeting_offline_bundle_v26_selfcheck_owner_a.md
git commit -m "chore(meeting): ignore offline bundle tar and add v26 selfcheck note"
git push origin HEAD:main
```

验收：

- 主线仅增加 `.gitignore` 规则与 1 个 notes。
- 不包含 `artifacts/meeting_assets/*.tar.gz` 的入库变更。

## 3) 并行性说明（给 B）

- A181–A183 不依赖 B；B 可并行继续写作/slide。
- A183 入库后，B 可选择性在 `meeting-handout-v26.md`/`meeting-index-v26.md` 追加一行提示：“离线 bundle 已自检 PASS”。

