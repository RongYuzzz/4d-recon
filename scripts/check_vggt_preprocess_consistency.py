#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from precompute_vggt_cache import (
    _index_camera_frames,
    _parse_camera_ids,
    _run_backend_dummy,
    _run_backend_vggt,
)


def _fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Sanity-check VGGT preprocess consistency (self-consistency + cache round-trip)"
    )
    ap.add_argument("--backend", choices=["dummy", "vggt"], default="dummy")
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--camera_ids", required=True)
    ap.add_argument("--frame_start", type=int, default=0)
    ap.add_argument("--num_frames", type=int, default=2)
    ap.add_argument("--phi_name", default="", help="dummy uses dummy_rgb; vggt uses depth/world_points")
    ap.add_argument("--phi_downscale", type=int, default=4)
    ap.add_argument("--vggt_model_id", default="facebook/VGGT-1B")
    ap.add_argument("--vggt_cache_dir", default="")
    ap.add_argument("--vggt_mode", choices=["crop", "pad"], default="crop")
    ap.add_argument("--dtype", choices=["float16", "float32"], default="float16")
    ap.add_argument("--self_tol", type=float, default=1e-6)
    ap.add_argument("--roundtrip_tol", type=float, default=5e-4)
    ap.add_argument("--cache_out_dir", default="")
    ap.add_argument("--keep_cache", action="store_true")
    return ap.parse_args()


def _build_frame_maps(data_dir: Path, camera_names: list[str], frame_indices: list[int]) -> dict[str, dict[int, Path]]:
    images_dir = data_dir / "images"
    if not images_dir.is_dir():
        _fail(f"missing images dir: {images_dir}")
    frame_maps: dict[str, dict[int, Path]] = {}
    for cam_name in camera_names:
        frame_map = _index_camera_frames(images_dir / cam_name)
        missing = [idx for idx in frame_indices if idx not in frame_map]
        if missing:
            _fail(
                f"camera '{cam_name}' missing frames for requested range: "
                f"{missing[:5]}{'...' if len(missing) > 5 else ''}"
            )
        frame_maps[cam_name] = frame_map
    return frame_maps


def _compute_online_phi(
    *,
    backend: str,
    frame_maps: dict[str, dict[int, Path]],
    camera_names: list[str],
    frame_indices: list[int],
    phi_name: str,
    vggt_model_id: str,
    vggt_cache_dir: str,
    vggt_mode: str,
    phi_downscale: int,
) -> np.ndarray:
    if backend == "dummy":
        phi, _conf, _input_size, _phi_size, _extras = _run_backend_dummy(
            frame_maps=frame_maps,
            camera_names=camera_names,
            frame_indices=frame_indices,
            phi_downscale=phi_downscale,
        )
        return phi.astype(np.float32, copy=False)

    phi, _conf, _input_size, _phi_size, _extras = _run_backend_vggt(
        frame_maps=frame_maps,
        camera_names=camera_names,
        frame_indices=frame_indices,
        phi_name=phi_name,
        token_layer_idx=23,
        token_proj_dim=32,
        token_proj_seed=20260225,
        token_proj_normalize=True,
        save_framediff_gate=False,
        framediff_top_p=0.10,
        vggt_model_id=vggt_model_id,
        vggt_cache_dir=vggt_cache_dir,
        vggt_mode=vggt_mode,
        phi_downscale=phi_downscale,
    )
    return phi.astype(np.float32, copy=False)


def _max_abs_diff(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        _fail(f"shape mismatch: {a.shape} vs {b.shape}")
    if a.size == 0:
        return 0.0
    return float(np.max(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def _run_cache_precompute(
    *,
    script_path: Path,
    data_dir: Path,
    out_dir: Path,
    camera_ids: str,
    frame_start: int,
    num_frames: int,
    backend: str,
    phi_name: str,
    phi_downscale: int,
    vggt_model_id: str,
    vggt_cache_dir: str,
    vggt_mode: str,
    dtype: str,
) -> None:
    cmd = [
        sys.executable,
        str(script_path),
        "--data_dir",
        str(data_dir),
        "--out_dir",
        str(out_dir),
        "--camera_ids",
        camera_ids,
        "--frame_start",
        str(frame_start),
        "--num_frames",
        str(num_frames),
        "--backend",
        backend,
        "--phi_name",
        phi_name,
        "--phi_downscale",
        str(phi_downscale),
        "--vggt_model_id",
        vggt_model_id,
        "--vggt_cache_dir",
        vggt_cache_dir,
        "--vggt_mode",
        vggt_mode,
        "--dtype",
        dtype,
        "--overwrite",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        _fail(
            "precompute_vggt_cache.py failed during round-trip check.\n"
            f"cmd: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def main() -> int:
    args = parse_args()

    if args.frame_start < 0:
        _fail("--frame_start must be >= 0")
    if args.num_frames <= 0:
        _fail("--num_frames must be > 0")
    if args.phi_downscale <= 0:
        _fail("--phi_downscale must be >= 1")
    if args.self_tol < 0 or args.roundtrip_tol < 0:
        _fail("--self_tol and --roundtrip_tol must be >= 0")

    phi_name = args.phi_name.strip()
    if not phi_name:
        phi_name = "dummy_rgb" if args.backend == "dummy" else "depth"
    if args.backend == "dummy" and phi_name != "dummy_rgb":
        _fail("backend=dummy requires --phi_name dummy_rgb")

    data_dir = Path(args.data_dir).resolve()
    camera_names = _parse_camera_ids(args.camera_ids)
    frame_indices = [args.frame_start + i for i in range(args.num_frames)]
    frame_maps = _build_frame_maps(data_dir, camera_names, frame_indices)

    phi_a = _compute_online_phi(
        backend=args.backend,
        frame_maps=frame_maps,
        camera_names=camera_names,
        frame_indices=frame_indices,
        phi_name=phi_name,
        vggt_model_id=args.vggt_model_id,
        vggt_cache_dir=args.vggt_cache_dir,
        vggt_mode=args.vggt_mode,
        phi_downscale=args.phi_downscale,
    )
    phi_b = _compute_online_phi(
        backend=args.backend,
        frame_maps=frame_maps,
        camera_names=camera_names,
        frame_indices=frame_indices,
        phi_name=phi_name,
        vggt_model_id=args.vggt_model_id,
        vggt_cache_dir=args.vggt_cache_dir,
        vggt_mode=args.vggt_mode,
        phi_downscale=args.phi_downscale,
    )

    self_diff = _max_abs_diff(phi_a, phi_b)
    self_ok = self_diff <= args.self_tol
    print(
        f"[Sanity] GT self-consistency: max_abs_diff={self_diff:.8f}, "
        f"tol={args.self_tol:.8f}, ok={self_ok}"
    )

    script_path = Path(__file__).resolve().parent / "precompute_vggt_cache.py"
    if not script_path.exists():
        _fail(f"missing precompute script: {script_path}")

    cleanup_cache_dir: Path | None = None
    if args.cache_out_dir.strip():
        cache_dir = Path(args.cache_out_dir).resolve()
        cache_dir.mkdir(parents=True, exist_ok=True)
    else:
        cleanup_cache_dir = Path(tempfile.mkdtemp(prefix="vggt_preprocess_consistency_"))
        cache_dir = cleanup_cache_dir

    try:
        _run_cache_precompute(
            script_path=script_path,
            data_dir=data_dir,
            out_dir=cache_dir,
            camera_ids=args.camera_ids,
            frame_start=args.frame_start,
            num_frames=args.num_frames,
            backend=args.backend,
            phi_name=phi_name,
            phi_downscale=args.phi_downscale,
            vggt_model_id=args.vggt_model_id,
            vggt_cache_dir=args.vggt_cache_dir,
            vggt_mode=args.vggt_mode,
            dtype=args.dtype,
        )
        npz_path = cache_dir / "gt_cache.npz"
        if not npz_path.exists():
            _fail(f"round-trip cache missing npz: {npz_path}")

        cached = np.load(npz_path, allow_pickle=True)
        if "phi" not in cached.files:
            _fail(f"'phi' missing in cache npz keys={cached.files}")
        phi_cached = cached["phi"].astype(np.float32, copy=False)
        roundtrip_diff = _max_abs_diff(phi_a, phi_cached)
        roundtrip_ok = roundtrip_diff <= args.roundtrip_tol
        print(
            f"[Sanity] cache round-trip: max_abs_diff={roundtrip_diff:.8f}, "
            f"tol={args.roundtrip_tol:.8f}, ok={roundtrip_ok}"
        )
    finally:
        if cleanup_cache_dir is not None and not args.keep_cache:
            shutil.rmtree(cleanup_cache_dir, ignore_errors=True)

    if not self_ok:
        print("FAIL: GT self-consistency check failed")
        return 1
    if not roundtrip_ok:
        print("FAIL: cache round-trip check failed")
        return 1

    print("PASS: VGGT preprocess consistency checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
