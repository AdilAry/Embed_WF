#!/usr/bin/env bash
# Install (or refresh) the slash commands and the "How I work" file for the
# agents on this machine: the short-loop core (/start, /wrap, /judge) from
# workflow/, plus this kit's embedded commands (/define, /commission, ...)
# from prompts/.
#
#     bash ~/Embed_WF/tools/install-workflow.sh [--copy]
#
# The commands are LINKED into each agent's commands folder, so after a
# `git pull` in ~/Embed_WF they are up to date with nothing to re-run. With
# --copy they are copied instead (then run this again after each update).
# All the work is done by workflow/install.sh; read that for the details.
set -euo pipefail
REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
bash "$REPO/workflow/install.sh" "$@" "$REPO/prompts"

# Commands this kit used to ship; /start and /wrap replaced them. A copy left
# behind by an older install would still be offered, so remove it.
for dir in "${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/prompts" "$HOME/.claude/commands"; do
  for old in build-loop wrap-up; do
    if [[ -f "$dir/$old.md" ]]; then rm -f "$dir/$old.md"; echo "removed retired /$old from $dir"; fi
  done
done
