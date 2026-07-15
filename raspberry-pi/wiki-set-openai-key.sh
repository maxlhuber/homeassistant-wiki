#!/bin/bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte mit sudo ausführen." >&2
  exit 1
fi
if [ ! -t 0 ]; then
  echo "Der Schlüssel muss interaktiv eingegeben werden." >&2
  exit 1
fi

read -r -s -p "Neuen OpenAI-API-Schlüssel eingeben: " API_KEY
printf '\n'
if [[ ! "${API_KEY}" =~ ^sk-[A-Za-z0-9_-]{20,}$ ]]; then
  unset API_KEY
  echo "Der Schlüssel hat nicht das erwartete Format." >&2
  exit 1
fi

install -d -m 0700 /etc/homeassistant-wiki
TEMPORARY="$(mktemp /etc/homeassistant-wiki/.openai-api-key.XXXXXX)"
trap 'rm -f "${TEMPORARY}"' EXIT
chmod 0600 "${TEMPORARY}"
printf '%s\n' "${API_KEY}" >"${TEMPORARY}"
unset API_KEY
chown root:root "${TEMPORARY}"
mv -f "${TEMPORARY}" /etc/homeassistant-wiki/openai-api-key
trap - EXIT

echo "Der neue Schlüssel wurde geschützt gespeichert und wird beim nächsten Wochenlauf verwendet."
