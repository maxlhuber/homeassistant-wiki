#!/bin/bash
set -euo pipefail

: "${CREDENTIALS_DIRECTORY:?Systemd-Credentials fehlen.}"

read_credential() {
  local name="$1"
  local path="${CREDENTIALS_DIRECTORY}/${name}"
  test -f "${path}"
  tr -d '\r\n' <"${path}"
}

mqtt_username="$(read_credential mqtt_username)"
mqtt_password="$(read_credential mqtt_password)"
mqtt_topic="$(read_credential mqtt_topic)"
trigger_payload="$(read_credential mqtt_payload)"

test -n "${mqtt_username}"
test -n "${mqtt_password}"
test -n "${mqtt_topic}"
test -n "${trigger_payload}"

mqtt_host="${WIKI_MQTT_HOST:-192.168.1.100}"
mqtt_port="${WIKI_MQTT_PORT:-1883}"
last_start=0

while true; do
  message="$(/usr/bin/mosquitto_sub \
    --quiet \
    --host "${mqtt_host}" \
    --port "${mqtt_port}" \
    --username "${mqtt_username}" \
    --pw "${mqtt_password}" \
    --topic "${mqtt_topic}" \
    --qos 1 \
    -R \
    -C 1 \
    -F '%p')"

  if [ "${message}" != "${trigger_payload}" ]; then
    continue
  fi

  now="$(date +%s)"
  if systemctl is-active --quiet wiki-weekly.service; then
    echo "Manueller Wiki-Start ignoriert: Lauf ist bereits aktiv."
    continue
  fi
  if [ $((now - last_start)) -lt 60 ]; then
    echo "Manueller Wiki-Start durch Zeitbegrenzung ignoriert."
    continue
  fi

  last_start="${now}"
  echo "Manuelle Wiki-Aktualisierung über Home Assistant gestartet."
  systemctl start --no-block wiki-weekly.service
done
