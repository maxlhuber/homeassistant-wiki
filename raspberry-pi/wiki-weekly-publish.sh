#!/bin/bash
set -euo pipefail

REPO_DIR="${WIKI_REPO_DIR:-/srv/homeassistant-wiki/source}"
STATE_DIR="${WIKI_STATE_DIR:-/var/lib/homeassistant-wiki}"
PYTHON="${WIKI_PYTHON:-/opt/homeassistant-wiki-venv/bin/python}"
RUNNER_DIR="${WIKI_RUNNER_DIR:-/opt/homeassistant-wiki-runner}"
WEBHOOK_FILE="${CREDENTIALS_DIRECTORY}/ha_webhook_url"
QUEUE="${STATE_DIR}/notification-queue.json"

exec 9>"${STATE_DIR}/notification.lock"
flock 9

if [ ! -f "${STATE_DIR}/publish-ready" ]; then
  exit 0
fi
rm -f "${STATE_DIR}/publish-ready"

notify_kind() {
  runuser -u wikiadmin -- "${PYTHON}" "${RUNNER_DIR}/wiki_notify.py" \
    --webhook-file "${WEBHOOK_FILE}" \
    --queue "${QUEUE}" \
    --kind "$1" >/dev/null 2>&1 || true
}

if /usr/local/sbin/wiki-publish-static; then
  notify_kind update_success
else
  notify_kind deploy_rolled_back
  touch "${STATE_DIR}/failure-handled"
  exit 1
fi
