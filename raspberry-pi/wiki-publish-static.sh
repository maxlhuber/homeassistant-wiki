#!/bin/bash
set -euo pipefail

CANDIDATE="${WIKI_PUBLISH_CANDIDATE:-/var/lib/homeassistant-wiki/publish-site}"
RELEASES_DIR="/var/www/homeassistant-wiki-releases"
CURRENT_LINK="/var/www/homeassistant-wiki-current"
RELEASE_DIR="${RELEASES_DIR}/release-$(date +%Y%m%d%H%M%S)-$$"
OLD_TARGET=""
SWITCHED=0

test -d "${CANDIDATE}"
test ! -L "${CANDIDATE}"
test -s "${CANDIDATE}/index.html"
grep -Fq "Unser Zuhause" "${CANDIDATE}/index.html"

UNSAFE="$(find -P "${CANDIDATE}" -xdev -mindepth 1 \
  ! \( -type f -o -type d \) -print -quit)"
test -z "${UNSAFE}"
test -z "$(find -P "${CANDIDATE}" -xdev -type f -links +1 -print -quit)"
test -z "$(find -P "${CANDIDATE}" -xdev -type f -size +64M -print -quit)"

FILE_COUNT="$(find -P "${CANDIDATE}" -xdev -type f -printf '.\n' | wc -l)"
TOTAL_BYTES="$(find -P "${CANDIDATE}" -xdev -type f -printf '%s\n' \
  | awk '{sum += $1} END {print sum + 0}')"
test "${FILE_COUNT}" -gt 0
test "${FILE_COUNT}" -le 20000
test "${TOTAL_BYTES}" -le 536870912

install -d -m 0755 "${RELEASES_DIR}" "${RELEASE_DIR}"

cleanup_failed_release() {
  local exit_code="${1:-1}"
  trap - ERR INT TERM
  rm -f -- "${CURRENT_LINK}.new"
  if [ "${SWITCHED}" -eq 1 ]; then
    if [ -n "${OLD_TARGET}" ] && [ -d "${OLD_TARGET}" ]; then
      ln -s "${OLD_TARGET}" "${CURRENT_LINK}.new"
      mv -Tf "${CURRENT_LINK}.new" "${CURRENT_LINK}"
      systemctl reload nginx.service || true
    else
      rm -f -- "${CURRENT_LINK}"
    fi
  fi
  rm -rf -- "${RELEASE_DIR}"
  exit "${exit_code}"
}
trap 'cleanup_failed_release $?' ERR
trap 'cleanup_failed_release 130' INT
trap 'cleanup_failed_release 143' TERM

cp -a --no-preserve=ownership -- "${CANDIDATE}/." "${RELEASE_DIR}/"
test -z "$(find -P "${RELEASE_DIR}" -xdev -mindepth 1 \
  ! \( -type f -o -type d \) -print -quit)"
test -s "${RELEASE_DIR}/index.html"
grep -Fq "Unser Zuhause" "${RELEASE_DIR}/index.html"
find -P "${RELEASE_DIR}" -xdev -type d -exec chmod 0755 {} +
find -P "${RELEASE_DIR}" -xdev -type f -exec chmod 0644 {} +
chown -R www-data:www-data "${RELEASE_DIR}"

nginx -t
if [ -L "${CURRENT_LINK}" ]; then
  OLD_TARGET="$(readlink -f "${CURRENT_LINK}")"
fi
ln -s "${RELEASE_DIR}" "${CURRENT_LINK}.new"
mv -Tf "${CURRENT_LINK}.new" "${CURRENT_LINK}"
SWITCHED=1
systemctl reload nginx.service

HEALTHY=0
for _ in 1 2 3 4 5; do
  if curl --fail --silent --show-error --max-time 10 \
    --header 'Host: homeassistant-wiki.local' \
    http://127.0.0.1/ | grep -Fq "Unser Zuhause"; then
    HEALTHY=1
    break
  fi
  sleep 1
done
test "${HEALTHY}" -eq 1

SWITCHED=0
trap - ERR INT TERM
ls -1dt "${RELEASES_DIR}"/release-* 2>/dev/null \
  | tail -n +4 | xargs -r rm -rf -- || true
