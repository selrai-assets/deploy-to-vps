#!/usr/bin/env bash
# harden.sh — locks down a freshly booted Ubuntu box and creates the user that owns every
# automation. Every step checks first and only acts if something is missing, so running it
# again is always safe. Run on the box as the ubuntu admin user:
#   sudo bash harden.sh "ssh-ed25519 AAAA... deployer@machine"
set -euo pipefail

PUBKEY="${1:-}"
if [ -n "$PUBKEY" ]; then
  BOX_USER="automations"
  SSH_DIR="/home/${BOX_USER}/.ssh"
  # apt is Ubuntu's software installer; this stops it pausing to ask questions.
  export DEBIAN_FRONTEND=noninteractive
else
  echo "usage: sudo bash harden.sh \"<deployer ssh public key line>\"" >&2
  exit 1
fi

# 1. ufw — the box's firewall. Let SSH in, turn everything else away.
ufw allow OpenSSH >/dev/null
if ufw status | grep -q "Status: active"; then
  echo "OK: firewall (ufw) is on, SSH allowed"
else
  ufw --force enable >/dev/null
  echo "OK: firewall (ufw) turned on, SSH allowed"
fi

# 2. unattended-upgrades — the box installs its own security patches, unprompted.
if dpkg-query -W -f='${Status}' unattended-upgrades 2>/dev/null | grep -q "^install ok installed"; then
  echo "OK: unattended-upgrades already installed"
else
  apt-get update -qq
  apt-get install -y -qq unattended-upgrades
  echo "OK: unattended-upgrades installed"
fi
systemctl enable --now unattended-upgrades >/dev/null 2>&1
if systemctl is-enabled --quiet unattended-upgrades; then
  echo "OK: security updates apply themselves"
else
  echo "FAILED: unattended-upgrades did not enable" >&2
  exit 1
fi

# 3. Key-only SSH — a password can be guessed, an SSH key cannot.
DROPIN="/etc/ssh/sshd_config.d/60-deploy-to-vps.conf"
if grep -qx "PasswordAuthentication no" "$DROPIN" 2>/dev/null; then
  echo "OK: SSH already accepts keys only"
else
  printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\n' >"$DROPIN"
  chmod 644 "$DROPIN"
  sshd -t                        # config parses cleanly before we reload anything
  systemctl reload ssh
  echo "OK: SSH set to keys only, passwords off"
fi

# 4. The automations user — one Unix account that owns and runs every automation.
if id -u "$BOX_USER" >/dev/null 2>&1; then
  echo "OK: user ${BOX_USER} exists"
else
  adduser --disabled-password --gecos "" "$BOX_USER" >/dev/null
  echo "OK: user ${BOX_USER} created (no password, key access only)"
fi

# 5. Linger — lets this user's scheduled jobs run even when nobody is logged in.
if loginctl show-user "$BOX_USER" --property=Linger --value 2>/dev/null | grep -qx "yes"; then
  echo "OK: ${BOX_USER} timers run without anyone logged in"
else
  loginctl enable-linger "$BOX_USER"
  echo "OK: ${BOX_USER} timers set to run without anyone logged in"
fi

# 6. authorized_keys — the list of SSH keys allowed to deploy. One line per person.
install -d -m 700 -o "$BOX_USER" -g "$BOX_USER" "$SSH_DIR"
touch "${SSH_DIR}/authorized_keys"
if grep -qxF "$PUBKEY" "${SSH_DIR}/authorized_keys"; then
  echo "OK: this deployer's key is already trusted"
else
  printf '%s\n' "$PUBKEY" >>"${SSH_DIR}/authorized_keys"
  echo "OK: this deployer's key added"
fi
chmod 600 "${SSH_DIR}/authorized_keys"
chown "${BOX_USER}:${BOX_USER}" "${SSH_DIR}/authorized_keys"

# 7. The summary — every line above says what is now true of this box.
echo "OK: hardening finished — firewall on, patches automatic, key-only SSH, ${BOX_USER} ready"
