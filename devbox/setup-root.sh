#!/usr/bin/env bash
# Embed_WF dev box setup, part 1 of 2: system packages and permissions.
#
# Run ONCE on the Linux Mint laptop (ThinkPad T480s), from your normal admin
# account:
#
#     sudo bash setup-root.sh embdev
#
# "embdev" is the separate, NON-admin Linux user the AI agent will work as.
# It gets serial-port access, network-hotspot control and nothing else - so an
# agent running with few permission prompts can't read your old files or sudo.
#
# Safe to run again; every step checks before it changes anything.
set -euo pipefail

DEVUSER="${1:-}"
if [[ $EUID -ne 0 ]]; then echo "Run with sudo: sudo bash $0 <devuser>" >&2; exit 1; fi
if [[ -z "$DEVUSER" ]]; then echo "usage: sudo bash $0 <devuser>   (e.g. embdev)" >&2; exit 1; fi

step() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }

step "1/8 User '$DEVUSER'"
if id "$DEVUSER" >/dev/null 2>&1; then
  echo "exists"
else
  adduser --gecos "Embedded AI dev" "$DEVUSER"   # asks you for a password
fi
if id -nG "$DEVUSER" | tr ' ' '\n' | grep -qx sudo; then
  echo "WARNING: $DEVUSER is in the sudo group. For isolation, remove it: sudo deluser $DEVUSER sudo"
fi

step "2/8 Keep your own files private from $DEVUSER"
for h in /home/*; do
  owner="$(stat -c %U "$h")"
  if [[ "$owner" != "$DEVUSER" && -d "$h" ]]; then chmod 700 "$h" && echo "chmod 700 $h"; fi
done

step "3/8 Packages"
apt-get update
apt-get install -y \
  git make g++ curl wget ca-certificates jq unzip \
  python3 python3-venv python3-pip python3-serial python3-pytest \
  poppler-utils \
  mosquitto mosquitto-clients \
  network-manager iw bluez tmux \
  openssh-server

step "4/8 GitHub CLI (gh) from GitHub's official apt repo"
if ! command -v gh >/dev/null; then
  mkdir -p -m 755 /etc/apt/keyrings
  wget -qO /etc/apt/keyrings/githubcli-archive-keyring.gpg https://cli.github.com/packages/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list
  apt-get update && apt-get install -y gh
else
  echo "gh already installed"
fi

step "5/8 Serial ports"
# brltty (braille display daemon) grabs USB-serial chips like CH340/CP210x on
# Ubuntu-based distros, making the port vanish. Not needed unless you use a braille display.
if dpkg -s brltty >/dev/null 2>&1; then apt-get remove -y brltty; fi
usermod -aG dialout "$DEVUSER"
usermod -aG plugdev "$DEVUSER" 2>/dev/null || true
echo "$DEVUSER added to dialout (log out/in for it to apply)"

step "6/8 Let $DEVUSER control NetworkManager (for the bench-wifi test hotspot)"
# Newer polkit (Mint 22 / Ubuntu 24.04) reads JS rules ...
mkdir -p /etc/polkit-1/rules.d
cat >/etc/polkit-1/rules.d/50-embwf-networkmanager.rules <<EOF
polkit.addRule(function(action, subject) {
  if (action.id.indexOf("org.freedesktop.NetworkManager.") == 0 && subject.user == "$DEVUSER") {
    return polkit.Result.YES;
  }
});
EOF
# ... older polkit (Mint 21 / Ubuntu 22.04) reads .pkla files.
mkdir -p /etc/polkit-1/localauthority/50-local.d
cat >/etc/polkit-1/localauthority/50-local.d/50-embwf-networkmanager.pkla <<EOF
[Embed_WF bench hotspot]
Identity=unix-user:$DEVUSER
Action=org.freedesktop.NetworkManager.*
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF

step "7/8 Mosquitto: disable the system service (bench-mqtt runs its own)"
systemctl disable --now mosquitto 2>/dev/null || true

step "8/8 Firewall (only if ufw is active)"
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow from 10.42.0.0/24 to any port 1883 proto tcp comment "Embed_WF bench MQTT"
  ufw allow from 10.42.0.0/24 to any port 80 proto tcp comment "Embed_WF bench HTTP"
  ufw allow OpenSSH
else
  echo "ufw not active - nothing to do"
fi
systemctl enable --now ssh 2>/dev/null || systemctl enable --now sshd 2>/dev/null || true

cat <<EOF

Done. Next:
  1. Log out and log in as '$DEVUSER' (or from Windows: ssh $DEVUSER@$(hostname).local)
  2. gh auth login
  3. gh repo clone <your-github-user>/Embed_WF ~/Embed_WF
  4. bash ~/Embed_WF/devbox/setup-user.sh
EOF
