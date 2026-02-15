import ast
import sys
from pathlib import Path

trainer = Path('/root/projects/4d-recon/third_party/FreeTimeGsVanilla/src/simple_trainer_freetime_4d_pure_relocation.py')
source = trainer.read_text(encoding='utf-8')
module = ast.parse(source)

config = None
for node in module.body:
    if isinstance(node, ast.ClassDef) and node.name == 'Config':
        config = node
        break

if config is None:
    print('FAIL: Config class not found')
    sys.exit(1)

fields = set()
for stmt in config.body:
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        fields.add(stmt.target.id)

required = {
    'force_zero_velocity_for_t0',
    't0_debug_interval',
    't0_grad_log_path',
}
missing = sorted(required - fields)

if missing:
    print('FAIL: missing Config fields:', ', '.join(missing))
    sys.exit(1)

print('PASS: all required T0 config flags exist')
