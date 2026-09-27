#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${SAATHI_ENV:?Set SAATHI_ENV to development, local, or test}"
export SAATHI_ENV
cd "$ROOT_DIR/backend"
exec python3 -m app.demo.reset_demo
