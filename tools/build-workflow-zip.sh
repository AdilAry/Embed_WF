#!/usr/bin/env bash
# Build the standalone short-loop workflow archive from workflow/.
#
#     bash tools/build-workflow-zip.sh [output.zip]      default: dist/short_loop_workflow.zip
#
# The archive is the workflow/ folder and nothing else: the generic template
# for any software project, without the embedded parts of this kit. workflow/
# is its only source, so rebuild the archive instead of editing a copy of it.
set -euo pipefail
REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
OUT="${1:-$REPO/dist/short_loop_workflow.zip}"
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
if [[ -e "$OUT" ]]; then mv -f "$OUT" "$OUT.old"; fi
cd "$REPO"
zip -q -r -X "$OUT" workflow -x '*.DS_Store' '*/__pycache__/*'
if [[ -e "$OUT.old" ]]; then unlink "$OUT.old"; fi
unzip -l "$OUT" | tail -n +4 | awk 'NF==4 {print "  " $4}'
echo "wrote $OUT"
