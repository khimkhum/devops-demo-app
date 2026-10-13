#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
HEALTH_URL="${BASE_URL%/}/health"

echo "Checking: $HEALTH_URL"

if BODY=$(curl -fsS --connect-timeout 3 --max-time 5 "$HEALTH_URL"); then
    echo "Response: $BODY"
    echo "PASS: Health endpoint returned HTTP success."
else
    CURL_EXIT=$?
    echo "FAIL: Health request failed. curl exit code: $CURL_EXIT" >&2
    exit "$CURL_EXIT"
fi
