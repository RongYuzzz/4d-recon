from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

RUN_BASELINE = REPO_ROOT / "scripts" / "run_train_baseline_selfcap.sh"
RUN_PLANB_INIT = REPO_ROOT / "scripts" / "run_train_planb_init_selfcap.sh"
RUN_PLANB_FEAT_V2 = REPO_ROOT / "scripts" / "run_train_planb_feature_loss_v2_selfcap.sh"


FAKE_PY = r"""#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _log(script: str, args: list[str]) -> None:
    log_path = os.environ.get("FAKE_PY_LOG", "")
    if not log_path:
        return
    obj = {"script": script, "args": args}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=True) + "\n")


def _arg_after(args: list[str], key: str) -> str | None:
    try:
        idx = args.index(key)
    except ValueError:
        return None
    if idx + 1 >= len(args):
        return None
    return args[idx + 1]


def main() -> int:
    # Mimic `python - <args...>` used by some runners for small preflight checks.
    if len(sys.argv) >= 2 and sys.argv[1] == "-":
        sys.argv = sys.argv[1:]
        code = sys.stdin.read()
        scope: dict[str, object] = {"__name__": "__main__"}
        exec(compile(code, "<stdin>", "exec"), scope, scope)
        return 0

    if len(sys.argv) < 2:
        return 0

    script = sys.argv[1]
    args = sys.argv[2:]
    _log(script, args)

    script_name = Path(script).name
    if script_name == "combine_frames_fast_keyframes.py":
        out_path = _arg_after(args, "--output-path")
        if out_path:
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_bytes(b"fake-npz")
        return 0

    if script_name == "init_velocity_from_points.py":
        out_dir = _arg_after(args, "--out_dir")
        k = _arg_after(args, "--keyframe_step") or "5"
        if out_dir:
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"init_points_planb_step{k}.npz").write_bytes(b"fake-npz")
            (out / "velocity_stats.json").write_text("{\"ok\": true}\n", encoding="utf-8")
        return 0

    if script_name == "precompute_vggt_cache.py":
        out_dir = _arg_after(args, "--out_dir")
        if out_dir:
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "gt_cache.npz").write_bytes(b"fake-npz")
            (out / "meta.json").write_text("{\"ok\": true}\n", encoding="utf-8")
        return 0

    if script_name == "write_throughput_json.py":
        # runner calls: python write_throughput_json.py <result_dir>
        if args:
            result_dir = Path(args[0])
            stats = result_dir / "stats"
            stats.mkdir(parents=True, exist_ok=True)
            (stats / "throughput.json").write_text("{\"ok\": true}\n", encoding="utf-8")
        return 0

    if script_name == "simple_trainer_freetime_4d_pure_relocation.py":
        result_dir = _arg_after(args, "--result-dir")
        if result_dir:
            rd = Path(result_dir)
            rd.mkdir(parents=True, exist_ok=True)
            # Simulate the trainer overwriting cfg.yml at train() entry.
            (rd / "cfg.yml").write_text("fake: true\n", encoding="utf-8")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _read_trainer_args(log_path: Path) -> list[list[str]]:
    if not log_path.exists():
        return []
    out: list[list[str]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        obj = json.loads(line)
        if Path(obj["script"]).name == "simple_trainer_freetime_4d_pure_relocation.py":
            out.append(list(obj["args"]))
    return out


class RunnerArgsPassthroughTests(unittest.TestCase):
    def test_runners_should_forward_extra_args_eval_save_and_ckpt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runner_passthrough_", dir=REPO_ROOT) as td:
            root = Path(td)
            data_dir = root / "demo_data"
            (data_dir / "triangulation").mkdir(parents=True, exist_ok=True)
            (data_dir / "images").mkdir(parents=True, exist_ok=True)

            fake_py = root / "fake_python"
            fake_py.write_text(FAKE_PY, encoding="utf-8")
            fake_py.chmod(0o755)

            # 1) Baseline runner: EXTRA_TRAIN_ARGS + EVAL_STEPS/SAVE_STEPS passthrough.
            log1 = root / "baseline_log.jsonl"
            res_dir1 = root / "runs" / "baseline"
            env1 = os.environ.copy()
            env1.update(
                {
                    "VENV_PYTHON": str(fake_py),
                    "DATA_DIR": str(data_dir),
                    "GPU": "0",
                    "MAX_STEPS": "10",
                    "EVAL_STEPS": "1,2,3",
                    "SAVE_STEPS": "4,5",
                    "EXTRA_TRAIN_ARGS": "--lambda-duration-reg 0 --lambda-4d-reg 1e-2",
                    "FAKE_PY_LOG": str(log1),
                }
            )
            proc1 = subprocess.run(
                ["bash", str(RUN_BASELINE), str(res_dir1)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env1,
            )
            self.assertEqual(proc1.returncode, 0, msg=f"stderr:\n{proc1.stderr}")
            trainer_args1 = _read_trainer_args(log1)
            self.assertEqual(len(trainer_args1), 1)
            t1 = trainer_args1[0]
            self.assertIn("--eval-steps", t1)
            self.assertIn("1", t1)
            self.assertIn("2", t1)
            self.assertIn("3", t1)
            self.assertIn("--save-steps", t1)
            self.assertIn("4", t1)
            self.assertIn("5", t1)
            self.assertIn("--lambda-duration-reg", t1)
            self.assertIn("0", t1)
            self.assertIn("--lambda-4d-reg", t1)
            self.assertIn("1e-2", t1)

            # 2) Plan-B init runner: also forwards EXTRA_TRAIN_ARGS + EVAL/SAVE lists.
            log2 = root / "planb_init_log.jsonl"
            res_dir2 = root / "runs" / "planb_init"
            planb_out_dir = root / "plan_b"
            env2 = os.environ.copy()
            env2.update(
                {
                    "VENV_PYTHON": str(fake_py),
                    "DATA_DIR": str(data_dir),
                    "GPU": "0",
                    "MAX_STEPS": "10",
                    "EVAL_STEPS": "6,7",
                    "SAVE_STEPS": "8,9",
                    "PLANB_OUT_DIR": str(planb_out_dir),
                    "EXTRA_TRAIN_ARGS": "--lambda-duration-reg 0 --lambda-4d-reg 1e-3",
                    "FAKE_PY_LOG": str(log2),
                }
            )
            proc2 = subprocess.run(
                ["bash", str(RUN_PLANB_INIT), str(res_dir2)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env2,
            )
            self.assertEqual(proc2.returncode, 0, msg=f"stderr:\n{proc2.stderr}")
            trainer_args2 = _read_trainer_args(log2)
            self.assertEqual(len(trainer_args2), 1)
            t2 = trainer_args2[0]
            self.assertIn("--eval-steps", t2)
            self.assertIn("6", t2)
            self.assertIn("7", t2)
            self.assertIn("--save-steps", t2)
            self.assertIn("8", t2)
            self.assertIn("9", t2)
            self.assertIn("--lambda-duration-reg", t2)
            self.assertIn("--lambda-4d-reg", t2)

            # 3) Stage-2 runner: ckpt resume injects --ckpt-path and snapshots cfg.yml.
            log3 = root / "planb_feat_log.jsonl"
            res_dir3 = root / "runs" / "planb_feat_v2"
            res_dir3.mkdir(parents=True, exist_ok=True)
            (res_dir3 / "cfg.yml").write_text("phase0: true\n", encoding="utf-8")

            ckpt = root / "ckpt_149.pt"
            ckpt.write_bytes(b"fake-ckpt")

            vggt_cache = root / "vggt_cache"
            vggt_cache.mkdir(parents=True, exist_ok=True)
            (vggt_cache / "gt_cache.npz").write_bytes(b"fake-npz")

            env3 = os.environ.copy()
            env3.update(
                {
                    "VENV_PYTHON": str(fake_py),
                    "DATA_DIR": str(data_dir),
                    "GPU": "0",
                    "MAX_STEPS": "10",
                    "EVAL_STEPS": "1,2",
                    "SAVE_STEPS": "3,4",
                    "PLANB_OUT_DIR": str(planb_out_dir),
                    "VGGT_CACHE_OUT_DIR": str(vggt_cache),
                    "VGGT_FEAT_CACHE_NPZ": str(vggt_cache / "gt_cache.npz"),
                    "CKPT_PATH": str(ckpt),
                    "EXTRA_TRAIN_ARGS": "--lambda-duration-reg 0 --lambda-4d-reg 1e-4",
                    "FAKE_PY_LOG": str(log3),
                }
            )
            proc3 = subprocess.run(
                ["bash", str(RUN_PLANB_FEAT_V2), str(res_dir3)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env3,
            )
            self.assertEqual(proc3.returncode, 0, msg=f"stderr:\n{proc3.stderr}")

            snap = res_dir3 / "cfg_before_resume_from_ckpt_149.yml"
            self.assertTrue(snap.exists(), msg=f"missing cfg snapshot: {snap}")
            self.assertEqual(snap.read_text(encoding="utf-8"), "phase0: true\n")

            trainer_args3 = _read_trainer_args(log3)
            self.assertEqual(len(trainer_args3), 1)
            t3 = trainer_args3[0]
            self.assertIn("--ckpt-path", t3)
            self.assertIn(str(ckpt), t3)
            self.assertIn("--eval-steps", t3)
            self.assertIn("--save-steps", t3)
            self.assertIn("--lambda-duration-reg", t3)
            self.assertIn("--lambda-4d-reg", t3)


if __name__ == "__main__":
    unittest.main()

