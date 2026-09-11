#!/usr/bin/env bash
# Chief-of-Staff droplet first-run script
# Run as root on a fresh Ubuntu 24.04 droplet — works on BOTH bare images and
# the DO OpenClaw marketplace image (auto-detected).
# Installs Node 24 LTS + OpenClaw, provisions the `openclaw` user + systemd unit,
# clears legacy marketplace-image state if present, and verifies the gateway.
# NOTE: deliberately does NOT run `openclaw update` — on the DO marketplace image
# the updater's doctor reads the image's custom unit as a "foreign" service and
# refuses to maintain it. npm is the supported path on both image types.
set -euo pipefail

SERVICE_UNIT=openclaw.service
OC_USER=openclaw
OC_HOME=/home/$OC_USER

echo "==> apt update + upgrade"
export DEBIAN_FRONTEND=noninteractive
apt update && apt -y upgrade

# Node 24 LTS BEFORE openclaw update: current OpenClaw requires Node >=24.16 <25 or >=26.1,
# and the stock image ships Node 22, which makes `openclaw update` fail mid-flight.
echo "==> installing Node 24 LTS"
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt install -y nodejs

echo "==> node version check"
node --version

echo "==> installing OpenClaw via npm"
hash -r
npm install -g --allow-scripts=openclaw,@google/genai,koffi,tree-sitter-bash,protobufjs openclaw@latest
openclaw --version

# ---------------------------------------------------------------------------
# Detect install type by the presence of a gateway systemd unit (survives re-runs
# and partial setups; the user alone is not a reliable marker).
# ---------------------------------------------------------------------------
if [ -f /etc/systemd/system/$SERVICE_UNIT ]; then
  echo "==> existing $SERVICE_UNIT found (marketplace image or prior run)"
  BARE_IMAGE=0
else
  echo "==> no $SERVICE_UNIT — treating as bare install"
  BARE_IMAGE=1
fi

# Provision the `openclaw` user if missing (bare Ubuntu)
if ! id "$OC_USER" &>/dev/null; then
  echo "==> creating user $OC_USER"
  useradd -m -s /bin/bash "$OC_USER"
fi

# ---------------------------------------------------------------------------
# Legacy marketplace-image state: archive if present, skip cleanly if not
# ---------------------------------------------------------------------------
if [ -d /home/$OC_USER/.openclaw ]; then
  echo "==> archiving DO image legacy state (blocks newer gateway versions from booting)"
  systemctl stop "$SERVICE_UNIT" 2>/dev/null || true
  BACKUP=/root/legacy-migration-backup
  mkdir -p "$BACKUP"
  for f in \
    /home/$OC_USER/.openclaw/workspace/.openclaw/workspace-state.json \
    /home/$OC_USER/.openclaw/workspace/openclaw-workspace-state.json \
    /home/$OC_USER/.openclaw/agents/main/sessions/sessions.json \
    /home/$OC_USER/.openclaw/workspace/.attested; do
    if [ -e "$f" ]; then mv "$f" "$BACKUP/"; echo "archived: $f"; fi
  done
  rmdir /home/$OC_USER/.openclaw/workspace/.openclaw 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Home directory + workspace scaffold (idempotent)
# ---------------------------------------------------------------------------
echo "==> provisioning $OC_HOME/.openclaw"
mkdir -p /home/$OC_USER/.openclaw/workspace
chown -R $OC_USER:$OC_USER /home/$OC_USER/.openclaw

# ---------------------------------------------------------------------------
# systemd unit (only needed on bare images; marketplace image ships its own)
# ---------------------------------------------------------------------------
if [ "$BARE_IMAGE" = "1" ]; then
  echo "==> writing systemd unit $SERVICE_UNIT"
  cat > /etc/systemd/system/$SERVICE_UNIT <<EOF
[Unit]
Description=OpenClaw Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$OC_USER
WorkingDirectory=/home/$OC_USER/.openclaw
ExecStart=/usr/bin/env openclaw gateway --port 18789
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable "$SERVICE_UNIT"
fi

# ---------------------------------------------------------------------------
# Initial gateway onboarding (bare images only; image installs come pre-onboarded)
# Run BEFORE the systemd unit exists, otherwise `openclaw doctor` refuses
# ("Gateway service ownership could not be verified") and no config gets written.
# ---------------------------------------------------------------------------
if [ "$BARE_IMAGE" = "1" ]; then
  echo "==> initializing openclaw state for $OC_USER"
  sudo -u $OC_USER bash -lc 'openclaw onboard --non-interactive 2>/dev/null || openclaw doctor --fix --yes --non-interactive || true'
fi

# Fallback: guarantee a minimal local-mode config so the gateway can boot
# even if non-interactive onboarding did not produce one.
if [ ! -f $OC_HOME/.openclaw/openclaw.json ]; then
  echo "==> writing minimal local-mode config"
  cat > $OC_HOME/.openclaw/openclaw.json <<EOF
{
  "gateway": {
    "mode": "local",
    "bind": "loopback",
    "port": 18789
  }
}
EOF
  chown $OC_USER:$OC_USER $OC_HOME/.openclaw/openclaw.json
fi

# ---------------------------------------------------------------------------
# Persist a gateway auth token. Without this the gateway mints a fresh runtime
# token on every start, which breaks pairing across restarts. The token is
# stored in the config (mode 600); retrieve it later with:
#   sudo -u openclaw openclaw config get gateway.auth.token
# ---------------------------------------------------------------------------
AUTH_MODE=$(sudo -u $OC_USER bash -lc 'openclaw config get gateway.auth.mode' 2>/dev/null || true)
if [ "$AUTH_MODE" != "token" ]; then
  echo "==> persisting gateway auth token"
  sudo -u $OC_USER bash -lc 'openclaw config set gateway.auth.mode token'
  TOKEN=$(openssl rand -hex 32)
  sudo -u $OC_USER env OPENCLAW_SET_TOKEN="$TOKEN" bash -c 'openclaw config set gateway.auth.token "$OPENCLAW_SET_TOKEN"'
  unset TOKEN
  chown $OC_USER:$OC_USER $OC_HOME/.openclaw/openclaw.json
  chmod 600 $OC_HOME/.openclaw/openclaw.json
  echo "    (token stored in config — do not paste it into chat or tickets)"
fi

# ---------------------------------------------------------------------------
# Start + verify gateway
# ---------------------------------------------------------------------------
echo "==> starting gateway"
systemctl enable "$SERVICE_UNIT" 2>/dev/null || true
systemctl restart "$SERVICE_UNIT"
for i in 1 2 3 4 5 6; do
  sleep 10
  STATE=$(systemctl is-active "$SERVICE_UNIT" || true)
  echo "gateway state: $STATE"
  [ "$STATE" = "active" ] && break
done
ss -tlnp | grep -q 18789 && echo "gateway listening on 18789" || echo "NOT listening on 18789"
systemctl status "$SERVICE_UNIT" --no-pager | head -4
journalctl -u "$SERVICE_UNIT" -n 5 --no-pager 2>/dev/null || tail -2 /tmp/openclaw/openclaw-*.log 2>/dev/null || true

echo "==> gateway status"
openclaw gateway status

echo
echo "Next steps (see SETUP-WALKTHROUGH.md):"
echo "  1. From your laptop: scp template-chief-of-staff/chief-template.tar.gz root@<DROPLET_IP>:/tmp/ and untar into /home/openclaw/.openclaw/workspace/ (command in the walkthrough)"
echo "  2. Message the agent: Read FULLINSTRUCTIONS.md in your workspace and follow it."
echo "  3. Gateway auth token (for Control UI pairing): sudo -u openclaw openclaw config get gateway.auth.token"
