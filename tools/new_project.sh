#!/usr/bin/env bash
# Create a new ESP32 project from the Embed_WF template.
#
#   new-embedded-project <name> [parent-dir]      default parent: ~/projects
#
# Copies template/, refreshes the board reference from hardware/boards/, sets
# the project name, and makes the first git commit. Then:
#   cd ~/projects/<name> && pi          and type  /define
#
# For any other kind of software project use the short-loop starter instead:
#   new-project <name>                  (= workflow/new-project.sh)
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
if [[ "${1:-}" == "--generic" ]]; then shift; exec bash "$REPO/workflow/new-project.sh" "$@"; fi
NAME="${1:-}"
PARENT="${2:-$HOME/projects}"

if [[ ! "$NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "usage: $(basename "$0") <name> [parent-dir]" >&2
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

# Agents also load instruction files from every PARENT folder of a project (pi
# walks up to the filesystem root, Claude Code does the same for CLAUDE.md). A
# project created inside this kit, or inside another project, would silently
# get that folder's AGENTS.md as well. Refuse unless told otherwise.
mkdir -p "$PARENT"
dir="$(cd "$PARENT" && pwd)"
inherited=()
while :; do
  for f in AGENTS.override.md AGENTS.md CLAUDE.md; do
    [[ -f "$dir/$f" ]] && inherited+=("$dir/$f")
  done
  [[ "$dir" == "/" ]] && break
  dir="$(dirname "$dir")"
done
if [[ ${#inherited[@]} -gt 0 && "${ALLOW_PARENT_INSTRUCTIONS:-0}" != "1" ]]; then
  echo "Not creating $DEST: a project there would also load these instruction files" >&2
  echo "from its parent folders, in every session:" >&2
  printf '  %s\n' "${inherited[@]}" >&2
  echo "Choose a parent folder outside them, or set ALLOW_PARENT_INSTRUCTIONS=1 if that is intended." >&2
  exit 1
fi

cp -r "$REPO/template" "$DEST"
rm -rf "$DEST/build"
rm -f "$DEST/firmware/src/build_id.h"   # generated per build, never copied
mkdir -p "$DEST/docs/hardware"
cp "$REPO"/hardware/boards/*.md "$DEST/docs/hardware/"
sed -i "s/^#define FW_NAME \".*\"/#define FW_NAME \"$NAME\"/" "$DEST/firmware/src/config.h"
sed -i "s/^# Functional Specification — <project name>/# Functional Specification — $NAME/" "$DEST/docs/FSD.md"
sed -i "1s/.*/# $NAME/" "$DEST/README.md"
# The short-loop files carry the name as a "[project name]" marker.
grep -rl --exclude-dir=hardware -F '[project name]' "$DEST" | while read -r f; do
  sed -i "s/\[project name\]/$NAME/g" "$f"
done

cd "$DEST"
git init -q -b main
git add -A
git commit -q -m "Start $NAME from the Embed_WF template"
echo "Created $DEST"
echo
echo "Next:"
echo "  cd $DEST"
echo "  \$EDITOR docs/IDEA.md      # write your idea in plain words"
echo "  pi                         # then type: /define"
