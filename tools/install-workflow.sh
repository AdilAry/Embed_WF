#!/usr/bin/env bash
# Install (or refresh) the slash commands and the "How I work" file for the
# agents on this machine: the short-loop core (/start, /wrap, /judge) from the
# short-loop workflow, plus this kit's embedded commands (/define,
# /commission, ...) from prompts/.
#
#     bash ~/Embed_WF/tools/install-workflow.sh [--copy]
#
# The workflow is a separate repository. Install it first: clone it, run its
# install.sh once, and open a new terminal. That sets WORKFLOW_DIR, which is
# how this script finds it (WORKFLOW.md section 8). This script never guesses
# where the workflow is.
#
# The commands are LINKED into each agent's commands folder, so after a
# `git pull` here or in the workflow they are up to date with nothing to
# re-run. With --copy they are copied instead (then run this again after each
# update). The workflow's install.sh does all of the work.
set -euo pipefail
REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

if [[ -z "${WORKFLOW_DIR:-}" || ! -f "${WORKFLOW_DIR}/install.sh" ]]; then
  echo "The short-loop workflow was not found: WORKFLOW_DIR is ${WORKFLOW_DIR:-not set}." >&2
  echo "Install the workflow first: clone its repository, run  bash <that folder>/install.sh" >&2
  echo "once, then open a new terminal (that sets WORKFLOW_DIR) and run this again." >&2
  exit 1
fi

bash "$WORKFLOW_DIR/install.sh" "$@" "$REPO/prompts"

# Commands this kit used to ship; /start and /wrap replaced them. A copy left
# behind by an older install would still be offered, so remove it.
for dir in "${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/prompts" "$HOME/.claude/commands"; do
  for old in build-loop wrap-up; do
    if [[ -f "$dir/$old.md" ]]; then rm -f "$dir/$old.md"; echo "removed retired /$old from $dir"; fi
  done
done
