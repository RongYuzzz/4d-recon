# Handoff: Plan-B + Weak Smoke200（Owner A -> Owner B）

- 日期：2026-02-26
- 计划：`~/docs/plans/2026-02-26-owner-a-planb-plus-weak-smoke200-and-go-nogo.md`
- 状态：已完成（Task 1-5 全部落地）

## 结果目录（可直接写入 v22/v23 pack）

- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200`
- `outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200`

## 本地对比表路径（不入库，可复现）

- `outputs/report_pack/scoreboard_smoke200_planb_plus_weak.md`

## 复现命令（Task 2/3）

说明：当前机器需把 venv 的 `bin` 放入 `PATH`，否则 `gsplat` 动态编译会报 `Ninja is required`。

```bash
cd /root/projects/4d-recon
VENV_BIN=/root/projects/4d-recon/third_party/FreeTimeGsVanilla/.venv/bin
PY=$VENV_BIN/python
TRAINER=third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py
DATA_DIR=data/selfcap_bar_8cam60f
PLANB_INIT_NPZ=outputs/plan_b/selfcap_bar_8cam60f/init_points_planb_step5.npz

# Task 2: control (zeros mask)
MASK_NPZ=outputs/cue_mining/selfcap_bar_8cam60f_zeros_control/pseudo_masks.npz
OUT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_control_weak_nocue_smoke200
PATH="$VENV_BIN:$PATH" CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$OUT" \
  --start-frame 0 --end-frame 60 \
  --max-steps 200 --eval-steps 200 --save-steps 200 \
  --seed 42 \
  --train-camera-names 02,03,04,05,06,07 \
  --val-camera-names 08 --test-camera-names 09 \
  --eval-sample-every 1 --eval-sample-every-test 1 \
  --render-traj-path fixed --global-scale 6 \
  --pseudo-mask-npz "$MASK_NPZ" \
  --pseudo-mask-weight 0.5 \
  --pseudo-mask-end-step 600 \
  --eval-on-test
python3 scripts/write_throughput_json.py "$OUT"

# Task 3: ours-weak (diff mask)
MASK_NPZ=outputs/cue_mining/selfcap_bar_8cam60f_v1/pseudo_masks.npz
OUT=outputs/protocol_v1/selfcap_bar_8cam60f/planb_ours_weak_smoke200_w0.3_end200
PATH="$VENV_BIN:$PATH" CUDA_VISIBLE_DEVICES=0 "$PY" "$TRAINER" default_keyframe_small \
  --data-dir "$DATA_DIR" \
  --init-npz-path "$PLANB_INIT_NPZ" \
  --result-dir "$OUT" \
  --start-frame 0 --end-frame 60 \
  --max-steps 200 --eval-steps 200 --save-steps 200 \
  --seed 42 \
  --train-camera-names 02,03,04,05,06,07 \
  --val-camera-names 08 --test-camera-names 09 \
  --eval-sample-every 1 --eval-sample-every-test 1 \
  --render-traj-path fixed --global-scale 6 \
  --pseudo-mask-npz "$MASK_NPZ" \
  --pseudo-mask-weight 0.3 \
  --pseudo-mask-end-step 200 \
  --eval-on-test
python3 scripts/write_throughput_json.py "$OUT"
```

