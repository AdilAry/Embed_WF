#!/usr/bin/env bash
# Install (or refresh) the short-loop workflow for the agents on this machine.
#
#     bash ~/Embed_WF/tools/install-workflow.sh
#
# What it does, for each agent harness it finds:
#   - copies prompts/*.md to where that harness looks for slash commands, so
#     /start, /wrap, /judge, /define, /commission ... exist in every project;
#   - installs user-level/AGENTS.md ("How I work") as the harness's global
#     instructions file, but ONLY if there is none yet. Your own edits are
#     never overwritten; the script tells you when the kit's copy is newer.
#
# The commands and the instructions are the same text for every harness: one
# source in this repo, copied out. Run this again after `git pull`.
#
#   pi           ~/.pi/agent/prompts/      ~/.pi/agent/AGENTS.md
#   Claude Code  ~/.claude/commands/       ~/.claude/CLAUDE.md
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
RETIRED="build-loop wrap-up"   # commands this kit used to ship; /start and /wrap replaced them

install_for() {   # <name> <commands-dir> <global-instructions-file>
  local name="$1" cmd_dir="$2" global="$3" f
  echo "$name:"
  mkdir -p "$cmd_dir" "$(dirname "$global")"
  for f in "$REPO"/prompts/*.md; do
    cp "$f" "$cmd_dir/"
    echo "  /$(basename "$f" .md)"
  done
  for f in $RETIRED; do
    if [[ -f "$cmd_dir/$f.md" ]]; then rm -f "$cmd_dir/$f.md"; echo "  removed retired /$f"; fi
  done
  if [[ ! -e "$global" ]]; then
    cp "$REPO/user-level/AGENTS.md" "$global"
    echo "  installed $global  <- open it once and fill the one [bracket]"
  elif ! cmp -s "$REPO/user-level/AGENTS.md" "$global"; then
    echo "  kept your $global (it differs from the kit's user-level/AGENTS.md;"
    echo "    compare with: diff \"$REPO/user-level/AGENTS.md\" \"$global\")"
  else
    echo "  $global is up to date"
  fi
}

found=0
if command -v pi >/dev/null 2>&1 || [[ -d "${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}" ]]; then
  install_for "pi" "${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/prompts" "${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/AGENTS.md"
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
echo "Done. In a running session, reload the commands (pi: /reload) or start a new session."
