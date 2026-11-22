#!/usr/bin/env bash
# Embed_WF dev box setup, part 1 of 2: system packages and permissions.
#
# Run ONCE on the dev box (ThinkPad T480s, Debian 13 "trixie" with KDE Plasma),
# from your own admin account:
#
#     sudo bash setup-root.sh embdev
#
# No sudo on your account (a root password was set at install)? Then as root:
#
#     su -
#     bash /home/<you>/Downloads/Embed_WF-master/devbox/setup-root.sh embdev
#
# "embdev" is the separate, NON-admin Linux user the AI agent will work as.
# It gets serial-port access, network-hotspot control and nothing else - so an
# agent that runs commands without asking (Claude Code does, for everything its
# allowlist covers) can't read your old files or sudo.
#
# Safe to run again; every step checks before it changes anything.
set -euo pipefail

# Debian's plain `su` (without the dash) keeps your own PATH, which has no
# /usr/sbin, so adduser and usermod would not be found. Add the sbin folders.
export PATH="/usr/local/sbin:/usr/sbin:/sbin:$PATH"

DEVUSER="${1:-}"
if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash $0 <devuser>   (no sudo? run  su -  first, then  bash <full path to this script> <devuser>)" >&2
  exit 1
fi
if [[ -z "$DEVUSER" ]]; then echo "usage: sudo bash $0 <devuser>   (e.g. embdev)" >&2; exit 1; fi

step() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }

step "1/10 User '$DEVUSER'"
if id "$DEVUSER" >/dev/null 2>&1; then
  echo "exists"
else
  adduser --comment "Embedded AI dev" "$DEVUSER"   # asks you for a password
fi
if id -nG "$DEVUSER" | tr ' ' '\n' | grep -qx sudo; then
  echo "WARNING: $DEVUSER is in the sudo group. For isolation, remove it: sudo deluser $DEVUSER sudo"
fi

step "2/10 Keep your own files private from $DEVUSER"
for h in /home/*; do
  owner="$(stat -c %U "$h")"
  if [[ "$owner" != "$DEVUSER" && -d "$h" ]]; then chmod 700 "$h" && echo "chmod 700 $h"; fi
done

step "3/10 Packages"
# dnsmasq-base and wpasupplicant: NetworkManager needs them for the bench-wifi
# hotspot (DHCP for the boards, access-point mode); Debian only recommends them.
# avahi-daemon + libnss-mdns: makes <hostname>.local reachable from Windows.
apt-get update
apt-get install -y \
  git make g++ curl wget ca-certificates jq unzip pciutils \
  python3 python3-venv python3-pip python3-serial python3-pytest \
  poppler-utils \
  mosquitto mosquitto-clients \
  network-manager dnsmasq-base wpasupplicant iw bluez tmux \
  avahi-daemon libnss-mdns \
  openssh-server

step "4/10 GitHub CLI (gh) from GitHub's official apt repo"
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

step "5/10 Serial ports"
# brltty (braille display daemon) grabs USB-serial chips like CH340/CP210x,
# making the port vanish. Some installs include it; it isn't needed unless you
# use a braille display.
if dpkg -s brltty >/dev/null 2>&1; then apt-get remove -y brltty; fi
usermod -aG dialout "$DEVUSER"
usermod -aG plugdev "$DEVUSER" 2>/dev/null || true
echo "$DEVUSER added to dialout (log out/in for it to apply)"

step "6/10 Wi-Fi and Bluetooth: firmware, and NetworkManager in charge of the Wi-Fi card"
# The T480s has an Intel Wireless 8265. Its Wi-Fi AND Bluetooth firmware is in
# Debian's firmware-iwlwifi package, from the non-free-firmware component. The
# official Debian 13 installer normally installs it; this checks.
if lspci -nn 2>/dev/null | grep -qi 'network controller.*intel'; then
  if dpkg -s firmware-iwlwifi >/dev/null 2>&1; then
    echo "firmware-iwlwifi: installed"
  elif apt-cache policy firmware-iwlwifi 2>/dev/null | grep -q 'Candidate: [0-9]'; then
    apt-get install -y firmware-iwlwifi
    echo "firmware-iwlwifi installed - reboot before using Wi-Fi or Bluetooth"
  else
    echo "WARNING: firmware-iwlwifi can't be installed: the non-free-firmware component isn't in the apt sources."
    echo "  Add 'non-free-firmware' after 'main' on each Debian line of /etc/apt/sources.list"
    echo "  (or on the Components: line of /etc/apt/sources.list.d/debian.sources), then run this script again."
  fi
else
  echo "no Intel wireless card found - firmware-iwlwifi not needed"
fi
# bench-wifi drives the Wi-Fi card through NetworkManager. If the card is listed
# in /etc/network/interfaces (the older ifupdown way), NetworkManager leaves it
# alone ("unmanaged") and the hotspot can't start.
wifi_dev="$(nmcli -t -f DEVICE,TYPE,STATE device 2>/dev/null | awk -F: '$2=="wifi"{print $1":"$3; exit}')" || true
if [[ -z "$wifi_dev" ]]; then
  echo "WARNING: NetworkManager sees no Wi-Fi device. If the firmware was just installed, reboot and run this again."
elif [[ "${wifi_dev#*:}" == unmanaged* ]]; then
  echo "WARNING: NetworkManager does not manage ${wifi_dev%%:*}, so bench-wifi can't use it."
  echo "  Remove the lines for ${wifi_dev%%:*} from /etc/network/interfaces (keep the 'lo' lines), then reboot."
elif [[ "${wifi_dev#*:}" == unavailable* ]]; then
  echo "WARNING: ${wifi_dev%%:*} is unavailable: Wi-Fi is switched off (check  rfkill list) or its firmware hasn't loaded (reboot)."
else
  echo "Wi-Fi device ${wifi_dev%%:*}: managed by NetworkManager (${wifi_dev#*:}) - good"
fi

step "7/10 Let $DEVUSER control NetworkManager (for the bench-wifi test hotspot)"
# Debian 13's polkit reads JavaScript rules from /etc/polkit-1/rules.d.
mkdir -p /etc/polkit-1/rules.d
cat >/etc/polkit-1/rules.d/50-embwf-networkmanager.rules <<EOF
polkit.addRule(function(action, subject) {
  if (action.id.indexOf("org.freedesktop.NetworkManager.") == 0 && subject.user == "$DEVUSER") {
    return polkit.Result.YES;
  }
});
EOF

# That rule lets $DEVUSER do everything NetworkManager offers, which includes
# reading the passwords of Wi-Fi networks saved on this machine. The agent runs
# as $DEVUSER, so don't leave your home Wi-Fi saved here: the dev box is on
# Ethernet anyway. List what is saved and show how to forget it.
saved_wifi="$(nmcli -t -f NAME,TYPE connection show 2>/dev/null | awk -F: '$2=="802-11-wireless" && $1!="bench-hotspot"{print $1}')" || true
if [[ -n "$saved_wifi" ]]; then
  echo "WARNING: these Wi-Fi networks are saved on this machine, and $DEVUSER (the AI agent) could read their passwords:"
  echo "$saved_wifi" | sed 's/^/    /'
  echo "  Forget each one you care about (the dev box uses Ethernet):  sudo nmcli connection delete \"<name>\""
else
  echo "no saved Wi-Fi networks - good"
fi

step "8/10 Mosquitto: disable the system service (bench-mqtt runs its own)"
systemctl disable --now mosquitto 2>/dev/null || true

step "9/10 Lid: keep running when the lid is closed on AC, even with nobody logged in"
# KDE's Power Management setting ("When laptop lid closed: Do nothing") applies
# only while someone is logged in to Plasma. With nobody logged in (the usual
# case: you work over SSH), systemd-logind decides, and by default it suspends.
# This drop-in makes it ignore the lid while on AC power; on battery it still
# suspends. It takes effect after the next reboot: restarting logind now could
# end the desktop session you may be running this from.
LID_CONF=/etc/systemd/logind.conf.d/50-embwf-lid.conf
mkdir -p /etc/systemd/logind.conf.d
cat >"$LID_CONF" <<'EOF'
# Embed_WF: the dev box sits closed on a shelf, on AC, reached over SSH.
[Login]
HandleLidSwitchExternalPower=ignore
EOF
echo "wrote $LID_CONF (active after the next reboot)"

step "10/10 Firewall (only if ufw is active) and SSH"
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
  1. Reboot (the lid setting, new firmware and $DEVUSER's dialout group apply then)
  2. Log in as '$DEVUSER', or from Windows: ssh $DEVUSER@$(hostname).local
  3. gh auth login
  4. gh repo clone adilary/embed_wf ~/Embed_WF
  5. bash ~/Embed_WF/devbox/setup-user.sh
EOF
