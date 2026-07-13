#!/bin/bash
set -euo pipefail

SOURCE_DIR="/srv/homeassistant-wiki/source"
RELEASES_DIR="/var/www/homeassistant-wiki-releases"
CURRENT_LINK="/var/www/homeassistant-wiki-current"
RELEASE_DIR="${RELEASES_DIR}/release-$(date +%Y%m%d%H%M%S)-$$"

install -d -m 0755 "${RELEASES_DIR}" "${RELEASE_DIR}"

cleanup_failed_release() {
  rm -rf -- "${RELEASE_DIR}" "${CURRENT_LINK}.new"
}
trap cleanup_failed_release ERR INT TERM

/opt/homeassistant-wiki-venv/bin/python -m mkdocs build \
  --clean \
  --strict \
  --config-file "${SOURCE_DIR}/mkdocs.yml" \
  --site-dir "${RELEASE_DIR}"

chown -R www-data:www-data "${RELEASE_DIR}"
ln -s "${RELEASE_DIR}" "${CURRENT_LINK}.new"
mv -Tf "${CURRENT_LINK}.new" "${CURRENT_LINK}"
trap - ERR INT TERM

systemctl reload nginx.service 2>/dev/null || true
ls -1dt "${RELEASES_DIR}"/release-* 2>/dev/null | tail -n +4 | xargs -r rm -rf --
