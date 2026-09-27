#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
if [ ! -f .env ]; then cp .env.example .env; fi
read -rsp "Paste GEMINI_API_KEY (input hidden): " KEY
echo
python - "$KEY" <<'PY'
from pathlib import Path
import sys
key=sys.argv[1]
p=Path('.env')
s=p.read_text()
lines=s.splitlines()
for i,line in enumerate(lines):
    if line.startswith('GEMINI_API_KEY='):
        lines[i]='GEMINI_API_KEY='+key
        break
else:
    lines.append('GEMINI_API_KEY='+key)
p.write_text('\n'.join(lines)+'\n')
PY
echo "Gemini key saved to backend/.env. Restart FastAPI."
