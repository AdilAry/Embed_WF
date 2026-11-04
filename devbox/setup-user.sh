#!/usr/bin/env bash
# Embed_WF dev box setup, part 2 of 2: tools for the agent's user account.
#
# Run as the dev user (e.g. embdev), NOT with sudo, from inside the clone:
#
#     bash ~/Embed_WF/devbox/setup-user.sh
#
# Installs: arduino-cli + ESP32 core + libraries, Claude Code, the Embed_WF
# skills (/define, /build-loop, ...), the bench-* commands, a Python venv for BLE.
# Safe to run again.
set -euo pipefail

if [[ $EUID -eq 0 ]]; then echo "Don't run this with sudo." >&2; exit 1; fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$HOME/.local/bin"
VENV="$HOME/.local/share/embwf/venv"
ESP32_INDEX="https://espressif.github.io/arduino-esp32/package_esp32_index.json"
# Keep in sync with template/Makefile
ESP32_CORE_VERSION="$(sed -n 's/^ESP32_CORE_VERSION ?= //p' "$REPO/template/Makefile")"
GFX_LIB_VERSION="$(sed -n 's/^GFX_LIB_VERSION    ?= //p' "$REPO/template/Makefile")"

step() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
mkdir -p "$BIN"
export PATH="$BIN:$PATH"

step "1/7 PATH"
if ! grep -q 'Embed_WF' "$HOME/.bashrc" 2>/dev/null; then
  cat >>"$HOME/.bashrc" <<'EOF'

# --- Embed_WF ---
export PATH="$HOME/.local/bin:$PATH"
EOF
  echo "added ~/.local/bin to PATH in ~/.bashrc"
fi

step "2/7 arduino-cli"
if ! command -v arduino-cli >/dev/null; then
  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR="$BIN" sh
fi
arduino-cli version
arduino-cli config init >/dev/null 2>&1 || true   # no-op if a config already exists
arduino-cli config set board_manager.additional_urls "$ESP32_INDEX"

step "3/7 ESP32 core $ESP32_CORE_VERSION + GFX Library for Arduino $GFX_LIB_VERSION (large download, be patient)"
arduino-cli core update-index
arduino-cli core install "esp32:esp32@$ESP32_CORE_VERSION"
arduino-cli lib install "GFX Library for Arduino@$GFX_LIB_VERSION"

step "4/7 Claude Code"
if ! command -v claude >/dev/null; then
  curl -fsSL https://claude.ai/install.sh | bash
fi
command -v claude >/dev/null && claude --version || echo "open a new terminal, then run: claude"

step "5/7 Embed_WF skills -> ~/.claude/skills (available in every project)"
mkdir -p "$HOME/.claude/skills"
for d in "$REPO"/skills/*/; do
  name="$(basename "$d")"
  ln -sfn "$d" "$HOME/.claude/skills/$name"
  echo "  /$name"
done

step "6/7 bench commands -> $BIN"
python3 -m venv --system-site-packages "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip bleak
for t in bench-wifi bench-mqtt; do
  chmod +x "$REPO/bench/$t"
  ln -sfn "$REPO/bench/$t" "$BIN/$t"
done
cat >"$BIN/bench-ble-scan" <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" "$REPO/bench/bench-ble-scan" "\$@"
EOF
chmod +x "$BIN/bench-ble-scan"
ln -sfn "$REPO/tools/new_project.sh" "$BIN/new-embedded-project"
echo "  bench-wifi, bench-mqtt, bench-ble-scan, new-embedded-project"

step "7/7 Checks"
id -nG | grep -qw dialout && echo "dialout: ok" || echo "dialout: NOT active yet - log out and back in"
git config --global user.name >/dev/null || echo "set: git config --global user.name 'Your Name'"
git config --global user.email >/dev/null || echo "set: git config --global user.email 'you@example.com'"
gh auth status >/dev/null 2>&1 && echo "gh: logged in" || echo "gh: run 'gh auth login'"

cat <<EOF

Done. Next:
  1. Open a NEW terminal (PATH changes), then run:  claude   and log in with your Claude account.
  2. Plug in a board and run:  arduino-cli board list
  3. Create your first project:  new-embedded-project hello-board
  4. Follow docs/GUIDE.md, part 4 ("First project").
EOF
