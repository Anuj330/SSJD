#!/usr/bin/env bash
# ── SSJD main app (FastAPI + React) — one-shot deploy for a GCP Compute Engine VM ──
# Run on a fresh Ubuntu 22.04 VM (browser SSH):
#   curl -fsSL https://raw.githubusercontent.com/Anuj330/SSJD/feat/leadger_money_lead/deploy/gcp-setup.sh | bash
#
# Auto-detects the external IP, installs Docker, clones the repo, generates
# secrets, and serves the app on port 80. Idempotent (keeps existing deploy.env).
set -euo pipefail

REPO_URL="https://github.com/Anuj330/SSJD.git"
BRANCH="feat/leadger_money_lead"
APP_DIR="$HOME/SSJD"

echo "▶ 1/6  Detecting external IP…"
IP=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" 2>/dev/null || true)
[ -z "$IP" ] && IP=$(curl -s https://api.ipify.org || echo "YOUR_VM_IP")
echo "   external IP: $IP"

echo "▶ 2/6  Adding swap (helps the frontend build on a 2 GB VM)…"
if ! sudo swapon --show | grep -q .; then
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile
  echo "   2 GB swap enabled"
else
  echo "   swap already present"
fi

echo "▶ 3/6  Installing Docker (if missing)…"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
fi

echo "▶ 4/6  Fetching code…"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$BRANCH" -q && git -C "$APP_DIR" checkout -q "$BRANCH" && git -C "$APP_DIR" pull -q
else
  git clone -q -b "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

echo "▶ 5/6  Preparing secrets (deploy.env)…"
if [ ! -f deploy.env ]; then
  ADMIN_PW=$(openssl rand -hex 6)
  cat > deploy.env <<EOF
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=ssjd_db
ADMIN_EMAIL=admin@ssjd.coop
ADMIN_PASSWORD=$ADMIN_PW
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
NOTIFY_WA_PROVIDER=console
EOF
  echo "   generated deploy.env (admin password: $ADMIN_PW)"
else
  echo "   deploy.env already exists — keeping it."
fi

echo "▶ 6/6  Building & starting the stack (first build ~5-8 min)…"
sudo docker compose --env-file deploy.env -f docker-compose.prod.yml up -d --build

echo ""
echo "✅ Done."
echo "   App   : http://$IP/"
echo "   Login : admin@ssjd.coop   (password in $APP_DIR/deploy.env)"
echo "   Tip   : cat $APP_DIR/deploy.env | grep ADMIN_PASSWORD"
