#!/usr/bin/env bash
# ── SSJD one-shot VM deploy (Oracle Always Free / any Ubuntu VM) ─────────────
# Run as a sudo-capable user on a fresh Ubuntu 22.04/24.04 VM:
#   curl -fsSL <raw-url>/deploy/vm-setup.sh | bash
# or copy it over and:  bash vm-setup.sh
#
# It installs Docker, opens the host firewall for HTTP, clones the repo,
# and brings up the production stack. Edit deploy.env when prompted.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Anuj330/SSJD.git}"
BRANCH="${BRANCH:-feat/leadger_money_lead}"
APP_DIR="${APP_DIR:-$HOME/SSJD}"

echo "▶ 1/5  Installing Docker…"
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl git
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
fi

echo "▶ 2/5  Opening host firewall for port 80…"
# Oracle Ubuntu images ship with a restrictive iptables INPUT chain.
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || true
sudo netfilter-persistent save 2>/dev/null || \
  (sudo apt-get install -y iptables-persistent && sudo netfilter-persistent save) || true

echo "▶ 3/5  Fetching code…"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$BRANCH" && git -C "$APP_DIR" checkout "$BRANCH" && git -C "$APP_DIR" pull
else
  git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

echo "▶ 4/5  Preparing deploy.env…"
if [ ! -f deploy.env ]; then
  cp deploy.env.example deploy.env
  echo "  → Generated deploy.env from template."
  echo "  → EDIT IT NOW:  nano $APP_DIR/deploy.env   (set DB/admin passwords, JWT secret, keys)"
  echo "  → Then re-run:  cd $APP_DIR && sg docker -c 'docker compose -f docker-compose.prod.yml up -d --build'"
  exit 0
fi

echo "▶ 5/5  Building & starting the stack…"
sg docker -c "docker compose -f docker-compose.prod.yml up -d --build"

echo ""
echo "✅ Done. App should be live at:  http://$(curl -s ifconfig.me || echo YOUR_VM_IP)/"
echo "   Admin login uses ADMIN_EMAIL / ADMIN_PASSWORD from deploy.env."
