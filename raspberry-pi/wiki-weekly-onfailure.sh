#!/bin/bash
set -euo pipefail

STATE_DIR="${WIKI_STATE_DIR:-/var/lib/homeassistant-wiki}"
PYTHON="${WIKI_PYTHON:-/opt/homeassistant-wiki-venv/bin/python}"
RUNNER_DIR="${WIKI_RUNNER_DIR:-/opt/homeassistant-wiki-runner}"
MARKER="${STATE_DIR}/failure-handled"

exec 9>"${STATE_DIR}/notification.lock"
flock 9

if [ -f "${MARKER}" ] && find "${MARKER}" -mmin -5 -print -quit | grep -q .; then
  rm -f "${MARKER}"
  exit 0
fi
rm -f "${MARKER}"

"${PYTHON}" "${RUNNER_DIR}/wiki_notify.py" \
  --webhook-file "${CREDENTIALS_DIRECTORY}/ha_webhook_url" \
  --queue "${STATE_DIR}/notification-queue.json" \
  --kind validation_failed >/dev/null 2>&1 || true
