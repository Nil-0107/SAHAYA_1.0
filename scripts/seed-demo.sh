#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${SAHAYA_ENV:?Set SAHAYA_ENV to development, local, or test}"
export SAHAYA_ENV
cd "$ROOT_DIR/backend"
exec python3 -m app.demo.seed_demo
