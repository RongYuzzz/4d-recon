from pathlib import Path
import sys


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


repo_root = Path(__file__).resolve().parents[2]
script = repo_root / "scripts/run_mvp_repro.sh"
text = script.read_text(encoding="utf-8")

required_snippets = [
    'SELFCAP_TAR="data/selfcap/bar-release.tar.gz"',
    'SELFCAP_OUT_DIR="data/selfcap_bar_8cam60f"',
    "adapt_selfcap_release_to_freetime.py",
    '--tar_gz',
    '--output_dir',
]

for snippet in required_snippets:
    if snippet not in text:
        fail(f"missing required default snippet: {snippet}")

print("PASS: run_mvp_repro defaults include canonical SelfCap tar/output + adapter invocation")
