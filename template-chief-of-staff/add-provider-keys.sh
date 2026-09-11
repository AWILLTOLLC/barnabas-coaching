#!/usr/bin/env bash
# add-provider-keys.sh — wire a customer's OpenRouter API key into an OpenClaw droplet
# Run as root on the droplet. Prompts for the API key (hidden input), stages it in a
# 0600 file, wires it into config as a SecretRef, proves the route, cleans up.
# Never prints or logs the key value.
set -euo pipefail

OC_USER=openclaw
OC_HOME=/home/$OC_USER
KEY_FILE=$OC_HOME/.openclaw/openrouter.key

echo "==> OpenRouter provider setup for $OC_USER"

# --- gather key (hidden prompt, never echoed) ---
read -rsp "Paste the customer's OpenRouter API key (sk-or-...): " API_KEY
echo
if [ -z "$API_KEY" ]; then
  echo "ERROR: empty key, aborting." >&2
  exit 1
fi
if [[ ! "$API_KEY" =~ ^sk-or- ]]; then
  echo "WARNING: key doesn't start with sk-or- — continuing anyway, but double-check it." >&2
fi

# --- stage key in a 0600 file owned by openclaw ---
install -m 600 -o "$OC_USER" -g "$OC_USER" /dev/null "$KEY_FILE"
printf '%s' "$API_KEY" > "$KEY_FILE"
unset API_KEY
echo "==> key staged at $KEY_FILE (mode 600, owned by $OC_USER)"

# --- wire into config as SecretRef (validated writes, no plaintext in config) ---
echo "==> registering SecretRef + provider"
sudo -u "$OC_USER" openclaw config set secrets.providers.openrouter_key_file \
  --provider-source file --provider-path "$KEY_FILE" \
  --provider-mode singleValue
sudo -u "$OC_USER" openclaw config set models.providers.openrouter.apiKey \
  --ref-provider openrouter_key_file --ref-source file --ref-id value

# --- prove the route end to end ---
echo "==> proving model route (this makes a real, billable call)"
if sudo -u "$OC_USER" openclaw agent --message "Reply with exactly: PROVIDER-PROOF-OK" 2>&1 | grep -q "PROVIDER-PROOF-OK"; then
  echo "==> PROVIDER-PROOF-OK — model route verified"
else
  echo "!! Probe did not return PROVIDER-PROOF-OK. Check output above." >&2
  echo "   The key stays staged at $KEY_FILE; do NOT delete it while troubleshooting." >&2
  exit 1
fi

# --- cleanup: config now reads the key from the SecretRef at runtime ---
rm -f "$KEY_FILE"
echo "==> staged key file removed (config holds only a reference to it)"

echo
echo "Done. Re-fire the agent trigger with:"
echo "  sudo -u $OC_USER openclaw agent --message \"Read FULLINSTRUCTIONS.md in your workspace and follow it.\""