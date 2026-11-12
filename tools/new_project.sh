#!/usr/bin/env bash
# Create a new short-loop project from the Embed_WF kit.
#
#   new-embedded-project <name> [parent-dir]     ESP32 project from template/
#   new-project <name> [parent-dir]              any other software project, from generic/
#                                                (same as: new_project.sh --generic <name>)
#   default parent: ~/projects
#
# Copies the starter, sets the project name, and makes the first git commit. Then:
#   cd ~/projects/<name> && pi          embedded: type /define     generic: fill AGENTS.md, then /start M0
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
KIND=embedded
if [[ "${1:-}" == "--generic" ]]; then KIND=generic; shift; fi
NAME="${1:-}"
PARENT="${2:-$HOME/projects}"

if [[ ! "$NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "usage: $(basename "$0") [--generic] <name> [parent-dir]" >&2
  echo "  name: lowercase letters, digits, - and _ (it becomes the GitHub repo name)" >&2
  exit 1
fi
DEST="$PARENT/$NAME"
if [[ -e "$DEST" ]]; then echo "$DEST already exists" >&2; exit 1; fi

# Check everything that can fail BEFORE creating the folder, so a failed run
# never leaves a half-made project behind.
if ! git config user.name >/dev/null || ! git config user.email >/dev/null; then
  echo "git does not know who you are yet. Run these once, then try again:" >&2
  echo "  git config --global user.name \"Your Name\"" >&2
  echo "  git config --global user.email \"you@example.com\"" >&2
  exit 1
fi

mkdir -p "$PARENT"
if [[ "$KIND" == generic ]]; then
  cp -r "$REPO/generic" "$DEST"
  mkdir -p "$DEST/docs/notes"
else
  cp -r "$REPO/template" "$DEST"
  rm -rf "$DEST/build"
  rm -f "$DEST/firmware/src/build_id.h"   # generated per build, never copied
  mkdir -p "$DEST/docs/hardware"
  cp "$REPO"/hardware/boards/*.md "$DEST/docs/hardware/"
  sed -i "s/^#define FW_NAME \".*\"/#define FW_NAME \"$NAME\"/" "$DEST/firmware/src/config.h"
  sed -i "s/^# Functional Specification — <project name>/# Functional Specification — $NAME/" "$DEST/docs/FSD.md"
  sed -i "1s/.*/# $NAME/" "$DEST/README.md"
fi
# The short-loop files carry the name as a "[project name]" marker.
grep -rl --exclude-dir=hardware -F '[project name]' "$DEST" | while read -r f; do
  sed -i "s/\[project name\]/$NAME/g" "$f"
done

cd "$DEST"
git init -q -b main
git add -A
git commit -q -m "Start $NAME from the Embed_WF $KIND starter"
echo "Created $DEST"
echo
echo "Next:"
echo "  cd $DEST"
if [[ "$KIND" == generic ]]; then
  echo "  fill in AGENTS.md and docs/plan.md; nothing may be left in [brackets]:"
  echo "      grep -n '\\[' AGENTS.md docs/plan.md"
  echo "  pi   (or: claude)          # then type: /start M0"
else
  echo "  \$EDITOR docs/IDEA.md      # write your idea in plain words"
  echo "  pi                         # then type: /define"
fi
