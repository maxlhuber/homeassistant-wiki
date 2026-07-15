#!/bin/bash
set -euo pipefail

REPO_DIR="${WIKI_REPO_DIR:-/srv/homeassistant-wiki/source}"
STATE_DIR="${WIKI_STATE_DIR:-/var/lib/homeassistant-wiki}"
PYTHON="${WIKI_PYTHON:-/opt/homeassistant-wiki-venv/bin/python}"
RUNNER_DIR="${WIKI_RUNNER_DIR:-/opt/homeassistant-wiki-runner}"

exec 9>"${STATE_DIR}/notification.lock"
if ! flock -n 9; then
  exit 0
fi

"${PYTHON}" "${RUNNER_DIR}/wiki_notify.py" \
  --webhook-file "${CREDENTIALS_DIRECTORY}/ha_webhook_url" \
  --queue "${STATE_DIR}/notification-queue.json" \
  --flush >/dev/null 2>&1 || true
