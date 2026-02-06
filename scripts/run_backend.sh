#!/usr/bin/env bash
# Start the Questionnaire Agent backend (from project root).
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT/backend"
"$PROJECT_ROOT/venv/bin/uvicorn" app:app --host 0.0.0.0 --port 8000 "$@"
