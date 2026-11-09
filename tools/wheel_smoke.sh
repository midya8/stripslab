#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cd "$root"
python - "$tmp/expected.json" <<'PY'
import json,sys
from stripslab import audit
from pathlib import Path
xs=json.loads(Path('docs/controls.json').read_text())
Path(sys.argv[1]).write_text(json.dumps([dict(input=c['input'],report=audit(c['input'])) for c in xs]))
PY
uv build --wheel --out-dir "$tmp/dist" "$root"
uv venv "$tmp/env"
uv pip install --python "$tmp/env/bin/python" "$tmp"/dist/*.whl
cp tools/verify_installed.py "$tmp/verify.py"
cd "$tmp"
PYTHONPATH= "$tmp/env/bin/python" -I "$tmp/verify.py" "$tmp/expected.json"
