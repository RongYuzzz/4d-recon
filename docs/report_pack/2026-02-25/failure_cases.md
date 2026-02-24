# Failure Cases (Mechanism-Level)

1. Scene scale / max_dist filtering can drop all Gaussians (fix via --global-scale).
2. render_traj_path=arc may hit singular matrix for degenerate camera layouts (use fixed).
3. Per-frame sparse with non-contiguous frame ids needs remap; otherwise train range mismatch.
