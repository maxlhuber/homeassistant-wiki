#!/bin/bash
set -euo pipefail

exec >>/var/log/homeassistant-wiki-setup.log 2>&1
echo "Wiki-Installation gestartet: $(date --iso-8601=seconds)"

if [ -d /boot/firmware ]; then
  BOOT_DIR="/boot/firmware"
else
  BOOT_DIR="/boot"
fi

export DEBIAN_FRONTEND=noninteractive
APT_OK=0
for ATTEMPT in $(seq 1 30); do
  if apt-get update; then
    APT_OK=1
    break
  fi
  echo "Netzwerk noch nicht bereit (Versuch ${ATTEMPT}/30)."
  sleep 10
done
if [ "${APT_OK}" -ne 1 ]; then
  echo "Paketquellen waren nicht erreichbar; systemd versucht es später erneut."
  exit 1
fi

apt-get install -y --no-install-recommends \
  nginx \
  python3 \
  python3-pip \
  python3-venv \
  rsync \
  curl \
  git \
  cifs-utils \
  util-linux \
  ca-certificates \
  avahi-daemon

install -d -m 0755 /srv/homeassistant-wiki/source
tar -xzf /usr/local/lib/homeassistant-wiki/wiki-payload.tar.gz -C /srv/homeassistant-wiki/source
chown -R wikiadmin:wikiadmin /srv/homeassistant-wiki

python3 -m venv /opt/homeassistant-wiki-venv
/opt/homeassistant-wiki-venv/bin/python -m pip install --upgrade pip
/opt/homeassistant-wiki-venv/bin/python -m pip install -r /srv/homeassistant-wiki/source/requirements.txt

cat >/usr/local/sbin/wiki-update <<'EOF'
#!/bin/bash
set -euo pipefail
SOURCE_DIR="/srv/homeassistant-wiki/source"
RELEASES_DIR="/var/www/homeassistant-wiki-releases"
CURRENT_LINK="/var/www/homeassistant-wiki-current"
RELEASE_DIR="${RELEASES_DIR}/release-$(date +%Y%m%d%H%M%S)-$$"
OLD_TARGET=""
SWITCHED=0
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
/opt/homeassistant-wiki-venv/bin/python -m mkdocs build \
  --clean \
  --strict \
  --config-file "${SOURCE_DIR}/mkdocs.yml" \
  --site-dir "${RELEASE_DIR}"
test -s "${RELEASE_DIR}/index.html"
grep -Fq "Unser Zuhause" "${RELEASE_DIR}/index.html"
nginx -t
chown -R www-data:www-data "${RELEASE_DIR}"
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
ls -1dt "${RELEASES_DIR}"/release-* 2>/dev/null | tail -n +4 | xargs -r rm -rf --
EOF
chmod 0755 /usr/local/sbin/wiki-update

cat >/etc/nginx/sites-available/homeassistant-wiki <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name homeassistant-wiki.local homeassistant-wiki _;

    root /var/www/homeassistant-wiki-current;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location = /gesund {
        access_log off;
        add_header Content-Type text/plain;
        return 200 "Wiki ist bereit\n";
    }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/homeassistant-wiki /etc/nginx/sites-enabled/homeassistant-wiki

/usr/local/sbin/wiki-update
nginx -t
systemctl enable --now nginx.service avahi-daemon.service ssh.service

install -d -m 0755 /var/lib/homeassistant-wiki
date --iso-8601=seconds >/var/lib/homeassistant-wiki/setup-complete
printf 'FERTIG: Das Wiki ist unter http://homeassistant-wiki.local/ erreichbar.\n' >"${BOOT_DIR}/WIKI-STATUS.txt"
systemctl disable homeassistant-wiki-setup.service

echo "Wiki-Installation abgeschlossen: $(date --iso-8601=seconds)"
