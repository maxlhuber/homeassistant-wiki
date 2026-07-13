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
