#!/usr/bin/env bash
# Rebuild chief-template.tar.gz from ./
# Run from the template-chief-of-staff directory (or anywhere; paths are relative to this script).
set -euo pipefail
cd "$(dirname "$0")/templatefiles"

OUT=../chief-template.tar.gz
SANITIZED=0

# Hard sanitization gate: none of these may appear in any shipped file.
if grep -rInE "Dru|Aaron|Williams|Lily|Barnabas|kaw\.cc|wizard|🧙|hermes_quickguide|100\.65\.203\.16|tailb4a099|apollo|Fremont|Phinney|Black Raven|Glimmer|biotech|erasei" \
    ./; then
  echo "SANITIZATION FAILURE: forbidden strings found in ./ (list above). Fix before shipping." >&2
  exit 1
fi

# Required files present?
for f in AGENTS.md IDENTITY.md SOUL.md USER.md DECISIONS.md ERRORS.md FULLINSTRUCTIONS.md \
         memory/MEMORY-L0.md memory/instincts.md memory/daily-note-TEMPLATE.md; do
  [ -f "./$f" ] || { echo "missing: templatefiles/$f" >&2; exit 1; }
done

tar -czf "$OUT" \
  "AGENTS.md" IDENTITY.md SOUL.md USER.md DECISIONS.md ERRORS.md FULLINSTRUCTIONS.md \
  memory/

echo "built: $OUT"
tar -tzf "$OUT"