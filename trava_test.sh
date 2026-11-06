#!/usr/bin/env bash
# Testa o regras.py com cards falsos — não toca no Anki nem na coleção.
set -euo pipefail
cd "$(dirname "$0")"
PYTHONDONTWRITEBYTECODE=1 python3 -I trava_test.py "$@"
