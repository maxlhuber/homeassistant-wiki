#!/bin/bash
set -euo pipefail

if [ -f /boot/firmware/cmdline.txt ]; then
  BOOT_DIR="/boot/firmware"
else
  BOOT_DIR="/boot"
fi
HOST_NAME="homeassistant-wiki"
ADMIN_USER="wikiadmin"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE4teMw9pTNQNSR1mmxmRtcpE5ybX5SXTlUzTfUpkZiY homeassistant-wiki@MAX-PC"
WIFI_SSID="__WIFI_SSID__"
WIFI_PASSWORD="__WIFI_PASSWORD__"
WIFI_COUNTRY="DE"

exec >"${BOOT_DIR}/wiki-firstboot.log" 2>&1
echo "Ersteinrichtung gestartet: $(date --iso-8601=seconds)"

if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_hostname "${HOST_NAME}"
else
  CURRENT_HOSTNAME="$(cat /etc/hostname | tr -d ' \t\n\r')"
  printf '%s\n' "${HOST_NAME}" >/etc/hostname
  sed -i "s/127.0.1.1.*${CURRENT_HOSTNAME}/127.0.1.1\t${HOST_NAME}/" /etc/hosts
fi

if ! id "${ADMIN_USER}" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "${ADMIN_USER}"
fi
usermod -aG sudo "${ADMIN_USER}"
passwd --lock "${ADMIN_USER}" || true

install -d -m 0700 -o "${ADMIN_USER}" -g "${ADMIN_USER}" "/home/${ADMIN_USER}/.ssh"
printf '%s\n' "${PUBLIC_KEY}" >"/home/${ADMIN_USER}/.ssh/authorized_keys"
chown "${ADMIN_USER}:${ADMIN_USER}" "/home/${ADMIN_USER}/.ssh/authorized_keys"
chmod 0600 "/home/${ADMIN_USER}/.ssh/authorized_keys"

install -d -m 0755 /etc/ssh/sshd_config.d
cat >/etc/ssh/sshd_config.d/20-homeassistant-wiki.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
EOF
systemctl enable ssh.service

# Die Prüfung darf den vollständigen Platzhalter nicht wiederholen: Beim
# Einsetzen der SSID würde sonst auch die Vergleichsseite ersetzt.
if [[ "${WIFI_SSID}" != __WIFI_* ]]; then
  if [ -x /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
    /usr/lib/raspberrypi-sys-mods/imager_custom set_wlan "${WIFI_SSID}" "${WIFI_PASSWORD}" "${WIFI_COUNTRY}"
  else
    install -d -m 0700 /etc/NetworkManager/system-connections
    cat >/etc/NetworkManager/system-connections/homeassistant-wiki-wifi.nmconnection <<EOF
[connection]
id=${WIFI_SSID}
uuid=8f86e992-e483-4c45-bb78-90ce4259a27b
type=wifi
interface-name=wlan0
autoconnect=true

[wifi]
mode=infrastructure
ssid=${WIFI_SSID}

[wifi-security]
key-mgmt=wpa-psk
psk=${WIFI_PASSWORD}

[ipv4]
method=auto

[ipv6]
addr-gen-mode=default
method=auto
EOF
    chmod 0600 /etc/NetworkManager/system-connections/homeassistant-wiki-wifi.nmconnection
  fi
  raspi-config nonint do_wifi_country "${WIFI_COUNTRY}" || true
  rfkill unblock wifi || true
fi

cat >/etc/sudoers.d/20-wikiadmin <<'EOF'
wikiadmin ALL=(ALL) NOPASSWD: ALL
EOF
chmod 0440 /etc/sudoers.d/20-wikiadmin

install -d -m 0755 /usr/local/lib/homeassistant-wiki
install -m 0644 "${BOOT_DIR}/wiki-payload.tar.gz" /usr/local/lib/homeassistant-wiki/wiki-payload.tar.gz
install -m 0755 "${BOOT_DIR}/wiki-setup.sh" /usr/local/sbin/homeassistant-wiki-setup

cat >/etc/systemd/system/homeassistant-wiki-setup.service <<'EOF'
[Unit]
Description=Home Assistant Wiki einmalig installieren
Wants=network-online.target
After=network-online.target
ConditionPathExists=!/var/lib/homeassistant-wiki/setup-complete

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/homeassistant-wiki-setup
Restart=on-failure
RestartSec=60
TimeoutStartSec=infinity

[Install]
WantedBy=multi-user.target
EOF
systemctl enable homeassistant-wiki-setup.service

CMDLINE="${BOOT_DIR}/cmdline.txt"
sed -i -E 's# ?systemd\.run=[^ ]+##g; s# ?systemd\.run_success_action=[^ ]+##g; s# ?systemd\.unit=kernel-command-line\.target##g; s#  +# #g' "${CMDLINE}"
rm -f "${BOOT_DIR}/firstrun.sh"
printf 'Grundkonfiguration abgeschlossen. Das Wiki wird nach dem Neustart installiert.\n' >"${BOOT_DIR}/WIKI-STATUS.txt"

sync
echo "Ersteinrichtung abgeschlossen: $(date --iso-8601=seconds)"
