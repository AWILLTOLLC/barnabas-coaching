#!/bin/bash
# Installs the Mac capture command for x-eval.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"
cp "$HERE/x-eval-capture" "$BIN/x-eval-capture"
chmod +x "$BIN/x-eval-capture"

cat <<EOF
✓ Installed $BIN/x-eval-capture

Bind it to a hotkey (one-time, ~30 seconds):

  1. Open the Shortcuts app → New Shortcut
  2. Add action: "Run Shell Script", set script to:
       $BIN/x-eval-capture
  3. Name it "Evaluate X post", then in Shortcut Details
     add a keyboard shortcut (e.g. ⌥⌘E)
  4. First run will ask to allow controlling your browser — allow it.

From then on: look at a tweet, hit the hotkey, and the verdict arrives on
your agent's usual channel. Raycast/Alfred/Hammerspoon users can bind the
same command their own way.
EOF
