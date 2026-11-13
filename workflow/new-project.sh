#!/usr/bin/env bash
# Create a new short-loop project from templates/project. Linux and macOS.
# On Windows, copy the folder by hand (WORKFLOW.md section 3).
#
#     bash new-project.sh <name> [parent-dir]        default parent: ~/projects
#
# Copies the starter, puts the project name in, and makes the first git commit.
set -euo pipefail

HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
NAME="${1:-}"
PARENT="${2:-$HOME/projects}"

if [[ ! "$NAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "usage: $(basename "$0") <name> [parent-dir]" >&2
  echo "  name: lowercase letters, digits, - and _ (it becomes the repo name)" >&2
  exit 1
fi
DEST="$PARENT/$NAME"
if [[ -e "$DEST" ]]; then echo "$DEST already exists" >&2; exit 1; fi

# Check everything that can fail BEFORE creating the folder.
if ! git config user.name >/dev/null || ! git config user.email >/dev/null; then
  echo "git does not know who you are yet. Run these once, then try again:" >&2
  echo "  git config --global user.name \"Your Name\"" >&2
  echo "  git config --global user.email \"you@example.com\"" >&2
  exit 1
fi

# Agents also load instruction files from every PARENT folder of a project (pi
# walks up to the filesystem root, Claude Code does the same for CLAUDE.md). A
# project created inside another project, or inside this kit, would silently
# get that folder's instructions as well. Refuse unless told otherwise.
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

cp -r "$HERE/templates/project" "$DEST"
mkdir -p "$DEST/docs/notes"
grep -rl -F '[project name]' "$DEST" | while read -r f; do
  sed -i.bak "s/\[project name\]/$NAME/g" "$f" && rm -f "$f.bak"
done

cd "$DEST"
git init -q -b main
git add -A
git commit -q -m "Start $NAME from the short-loop starter"
echo "Created $DEST"
echo
echo "Next:"
echo "  cd $DEST"
echo "  1. Fill in AGENTS.md and docs/plan.md. Delete the [IF ...] sections that don't apply,"
echo "     and docs/data.md / docs/ai_log.md if this is not a data / competition project."
echo "  2. Nothing may be left in brackets:   grep -n '\\[' AGENTS.md docs/plan.md"
echo "  3. Start your agent here and type:    /start M0"
