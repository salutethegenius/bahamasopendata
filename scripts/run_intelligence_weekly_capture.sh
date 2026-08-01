#!/usr/bin/env bash
# Weekly Intelligence imprint capture (America/Nassau calendar date).
#
# Usage (from repo root):
#   ./scripts/run_intelligence_weekly_capture.sh
#   ./scripts/run_intelligence_weekly_capture.sh 2026-08-01
#
# Example crontab (Mondays 06:15 America/Nassau — set TZ on the host or use UTC):
#   15 6 * * 1 cd /path/to/bahamasopedata && ./scripts/run_intelligence_weekly_capture.sh >> data/intelligence/logs/weekly_cron.log 2>&1

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${1:-}" ]]; then
  CAPTURE_DATE="$1"
else
  CAPTURE_DATE="$(TZ=America/Nassau date +%F)"
fi

PYTHON="${ROOT_DIR}/backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi

mkdir -p "${ROOT_DIR}/data/intelligence/logs"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting intelligence capture for ${CAPTURE_DATE}"
"$PYTHON" ingestion/intelligence/run_capture.py --date "${CAPTURE_DATE}"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Finished intelligence capture for ${CAPTURE_DATE}"
