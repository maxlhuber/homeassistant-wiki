#!/bin/bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte mit sudo ausführen." >&2
  exit 1
fi

REPO_DIR="${WIKI_REPO_DIR:-/srv/homeassistant-wiki/source}"
CONFIG_DIR="/etc/homeassistant-wiki"
MOUNT_POINT="/mnt/homeassistant-backups"
FSTAB_MARKER="# homeassistant-wiki-backups"
RUNNER_DIR="/opt/homeassistant-wiki-runner"

for required in \
  "${REPO_DIR}/requirements.txt" \
  "${REPO_DIR}/raspberry-pi/wiki-weekly.service" \
  "${REPO_DIR}/raspberry-pi/wiki-weekly.timer" \
  "${REPO_DIR}/raspberry-pi/wiki-notify-retry.service" \
  "${REPO_DIR}/raspberry-pi/wiki-notify-retry.timer" \
  "${REPO_DIR}/raspberry-pi/wiki-weekly-onfailure.service"; do
  test -f "${required}"
done

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends \
  ca-certificates cifs-utils curl git nginx python3-venv rsync util-linux

install -d -m 0700 "${CONFIG_DIR}"
if mountpoint -q "${MOUNT_POINT}"; then
  umount "${MOUNT_POINT}"
fi
install -d -m 0750 -o wikiadmin -g wikiadmin "${MOUNT_POINT}"
install -m 0644 "${REPO_DIR}/raspberry-pi/github_known_hosts" \
  "${CONFIG_DIR}/github-known-hosts"
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-update.sh" \
  /usr/local/sbin/wiki-update
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-weekly-update.sh" \
  /usr/local/sbin/wiki-weekly-update
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-weekly-publish.sh" \
  /usr/local/sbin/wiki-weekly-publish
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-publish-static.sh" \
  /usr/local/sbin/wiki-publish-static
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-notify-retry.sh" \
  /usr/local/sbin/wiki-notify-retry
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-weekly-onfailure.sh" \
  /usr/local/sbin/wiki-weekly-onfailure
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-set-openai-key.sh" \
  /usr/local/sbin/homeassistant-wiki-set-openai-key
install -m 0755 "${REPO_DIR}/raspberry-pi/wiki-approve-review.py" \
  /usr/local/sbin/homeassistant-wiki-approve-review

install -d -m 0755 -o root -g root "${RUNNER_DIR}"
for runner_file in \
  generate_docs.py weekly_update.py wiki_backup.py wiki_notify.py \
  wiki_openai.py wiki_snapshot.py wiki_ai_prompt.txt; do
  install -m 0644 -o root -g root "${REPO_DIR}/scripts/${runner_file}" \
    "${RUNNER_DIR}/${runner_file}"
done

if [ ! -e "${CONFIG_DIR}/openai-api-key" ]; then
  install -m 0600 -o root -g root /dev/null "${CONFIG_DIR}/openai-api-key"
fi
for secret in nas-credentials ha-backup-key ha-webhook-url openai-api-key; do
  test -f "${CONFIG_DIR}/${secret}"
  chown root:root "${CONFIG_DIR}/${secret}"
  chmod 0600 "${CONFIG_DIR}/${secret}"
done

cat >"${CONFIG_DIR}/weekly.env" <<'EOF'
WIKI_REPO_DIR=/srv/homeassistant-wiki/source
WIKI_STATE_DIR=/var/lib/homeassistant-wiki
WIKI_BACKUP_DIR=/mnt/homeassistant-backups
WIKI_RUNNER_DIR=/opt/homeassistant-wiki-runner
WIKI_MAX_BACKUP_AGE=691200
OPENAI_MODEL=gpt-5.4-nano-2026-03-17
EOF
chmod 0644 "${CONFIG_DIR}/weekly.env"

FSTAB_LINE="//nas.local/backup ${MOUNT_POINT} cifs ro,nosuid,nodev,noexec,_netdev,x-systemd.automount,x-systemd.idle-timeout=10min,x-systemd.mount-timeout=30s,credentials=${CONFIG_DIR}/nas-credentials,vers=3.0,iocharset=utf8,uid=wikiadmin,gid=wikiadmin,file_mode=0400,dir_mode=0500 0 0 ${FSTAB_MARKER}"
FSTAB_TMP="$(mktemp)"
grep -vF "${FSTAB_MARKER}" /etc/fstab >"${FSTAB_TMP}" || true
printf '%s\n' "${FSTAB_LINE}" >>"${FSTAB_TMP}"
install -m 0644 -o root -g root "${FSTAB_TMP}" /etc/fstab
rm -f "${FSTAB_TMP}"

python3 -m venv --upgrade /opt/homeassistant-wiki-venv
/opt/homeassistant-wiki-venv/bin/python -m pip install --disable-pip-version-check \
  -r "${REPO_DIR}/requirements.txt"

install -m 0644 "${REPO_DIR}/raspberry-pi/wiki-weekly.service" \
  /etc/systemd/system/wiki-weekly.service
install -m 0644 "${REPO_DIR}/raspberry-pi/wiki-weekly.timer" \
  /etc/systemd/system/wiki-weekly.timer
install -m 0644 "${REPO_DIR}/raspberry-pi/wiki-notify-retry.service" \
  /etc/systemd/system/wiki-notify-retry.service
install -m 0644 "${REPO_DIR}/raspberry-pi/wiki-notify-retry.timer" \
  /etc/systemd/system/wiki-notify-retry.timer
install -m 0644 "${REPO_DIR}/raspberry-pi/wiki-weekly-onfailure.service" \
  /etc/systemd/system/wiki-weekly-onfailure.service

chown -R wikiadmin:wikiadmin "${REPO_DIR}"
install -d -m 0700 -o wikiadmin -g wikiadmin /var/lib/homeassistant-wiki

systemctl daemon-reload
AUTOMOUNT_UNIT="$(systemd-escape --path --suffix=automount "${MOUNT_POINT}")"
systemctl start "${AUTOMOUNT_UNIT}"
timeout 30 ls "${MOUNT_POINT}" >/dev/null

systemd-analyze verify \
  /etc/systemd/system/wiki-weekly.service \
  /etc/systemd/system/wiki-weekly.timer \
  /etc/systemd/system/wiki-notify-retry.service \
  /etc/systemd/system/wiki-notify-retry.timer \
  /etc/systemd/system/wiki-weekly-onfailure.service
systemctl enable --now wiki-weekly.timer wiki-notify-retry.timer

echo "Wöchentliche Wiki-Aktualisierung ist installiert."
