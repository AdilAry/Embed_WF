#!/usr/bin/env bash
# Install (or refresh) the short-loop workflow for the agents on this machine.
# Linux and macOS. On Windows, use the PowerShell lines in WORKFLOW.md section 3.
#
#     bash install.sh [--copy] [extra-commands-dir ...]
#
# For each agent harness it finds (pi, Claude Code) it does two things:
#
#   1. Makes /start, /wrap and /judge exist in every project, by LINKING
#      templates/commands/*.md into the folder that harness reads commands from.
#      Linked, not copied: after a `git pull` (or an edit) in this folder the
#      commands are up to date at once, with nothing to re-run.
#      --copy copies the files instead. Use it if a harness does not show the
#      linked commands, or if this folder may move or be deleted. After a copy
#      install, run this script again whenever the commands change.
#      Extra directories given on the command line are installed the same way
#      (a kit built on this workflow passes its own commands folder).
#
#   2. Installs templates/user-level/AGENTS.md ("How I work") as that harness's
#      global instructions file, but ONLY if there is none yet. That file is
#      yours to edit, so it is always a copy and is never overwritten.
#
#   pi           ~/.pi/agent/prompts/      ~/.pi/agent/AGENTS.md
#   Claude Code  ~/.claude/commands/       ~/.claude/CLAUDE.md
set -euo pipefail

HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
MODE=link
SOURCES=("$HERE/templates/commands")
for arg in "$@"; do
  case "$arg" in
    --copy) MODE=copy ;;
    --link) MODE=link ;;
    -*) echo "usage: bash install.sh [--copy] [extra-commands-dir ...]" >&2; exit 1 ;;
    *) [[ -d "$arg" ]] || { echo "not a directory: $arg" >&2; exit 1; }
       SOURCES+=("$(cd "$arg" && pwd)") ;;
  esac
done

install_for() {   # <name> <commands-dir> <global-instructions-file>
  local name="$1" cmd_dir="$2" global="$3" src f dest
  echo "$name:"
  mkdir -p "$cmd_dir" "$(dirname "$global")"
  for src in "${SOURCES[@]}"; do
    for f in "$src"/*.md; do
      [[ -e "$f" ]] || continue
      dest="$cmd_dir/$(basename "$f")"
      # Remove what is there first: copying onto an old link would write through it.
      if [[ -L "$dest" || -f "$dest" ]]; then rm -f "$dest"; fi
      if [[ "$MODE" == link ]]; then ln -s "$f" "$dest"; else cp "$f" "$dest"; fi
      echo "  /$(basename "$f" .md)"
    done
  done
  # A link whose file is gone (a command that was removed or renamed) is only clutter.
  for dest in "$cmd_dir"/*.md; do
    if [[ -L "$dest" && ! -e "$dest" ]]; then rm -f "$dest"; echo "  removed dead link $(basename "$dest")"; fi
  done
  if [[ ! -e "$global" ]]; then
    cp "$HERE/templates/user-level/AGENTS.md" "$global"
    echo "  installed $global  <- open it once and fill the one [bracket]"
  elif ! cmp -s "$HERE/templates/user-level/AGENTS.md" "$global"; then
    echo "  kept your $global (it differs from templates/user-level/AGENTS.md;"
    echo "    compare with: diff \"$HERE/templates/user-level/AGENTS.md\" \"$global\")"
  else
    echo "  $global is up to date"
  fi
}

found=0
PI_DIR="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
if command -v pi >/dev/null 2>&1 || [[ -d "$PI_DIR" ]]; then
  install_for "pi" "$PI_DIR/prompts" "$PI_DIR/AGENTS.md"
  found=1
fi
if command -v claude >/dev/null 2>&1 || [[ -d "$HOME/.claude" ]]; then
  install_for "Claude Code" "$HOME/.claude/commands" "$HOME/.claude/CLAUDE.md"
  found=1
fi
if [[ $found -eq 0 ]]; then
  echo "No agent harness found (looked for pi and Claude Code). Install one, then run this again." >&2
  exit 1
fi
if [[ "$MODE" == link ]]; then
  echo "Done (linked). Type / in a new session: /start, /wrap and /judge must be offered."
  echo "If they are not, run:  bash \"$HERE/install.sh\" --copy"
else
  echo "Done (copied). Run this again whenever the commands change."
fi
