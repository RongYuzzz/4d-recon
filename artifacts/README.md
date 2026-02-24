# Artifacts (Local)

这个目录用于存放**不适合进 git**的本地大文件（例如 evidence pack 的 `*.tar.gz`、视频、checkpoint 备份）。

约定：
- `artifacts/report_packs/`：离线证据包（可直接拷走备份）。
- `artifacts/report_packs/SHA256SUMS.txt`：对应 tarball 的校验和（建议入库，保证可追溯）。

注意：
- 不要在这里放唯一副本。重要产物建议同步到外部存储。
- 若你执行 `git clean -xfd`，被 `.gitignore` 忽略的文件可能会被清理掉。

