#!/usr/bin/env bash
# ── SSJD Website CMS — one-shot deploy for a GCP Compute Engine VM ───────────
# Run on a fresh Ubuntu 22.04 VM (browser SSH or gcloud):
#   curl -fsSL https://raw.githubusercontent.com/Anuj330/SSJD/feat/leadger_money_lead/SSJD-website-cms/deploy/gcp-setup.sh | bash
#
# It auto-detects the VM's external IP, generates secrets, brings the stack up
# on port 80, and prints the URLs + admin login. Safe to re-run (idempotent):
# it keeps the existing .env so your admin password doesn't change.
set -euo pipefail

REPO_URL="https://github.com/Anuj330/SSJD.git"
BRANCH="feat/leadger_money_lead"
APP_DIR="$HOME/SSJD"
CMS_DIR="$APP_DIR/SSJD-website-cms"

echo "▶ 1/6  Detecting external IP…"
IP=$(curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" 2>/dev/null || true)
[ -z "$IP" ] && IP=$(curl -s https://api.ipify.org || true)
[ -z "$IP" ] && { echo "Could not detect external IP — set it manually in .env"; IP="REPLACE_ME"; }
echo "   external IP: $IP"

echo "▶ 2/6  Installing Docker (if missing)…"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
fi

echo "▶ 3/6  Fetching code…"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$BRANCH" -q && git -C "$APP_DIR" checkout -q "$BRANCH" && git -C "$APP_DIR" pull -q
else
  git clone -q -b "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$CMS_DIR"

echo "▶ 4/6  Serving on port 8080 (port 80 is the main app)…"
sed -i 's/"8001:8000"/"8080:8000"/' docker-compose.yml || true

echo "▶ 5/6  Preparing secrets (.env)…"
if [ ! -f .env ]; then
  ADMIN_PW=$(openssl rand -hex 8)
  cat > .env <<EOF
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=$(openssl rand -hex 50)
DEBUG=False
ALLOWED_HOSTS=$IP
CORS_ALLOWED_ORIGINS=http://$IP:8080
CSRF_TRUSTED_ORIGINS=http://$IP:8080
# HTTP-only deployment (no TLS yet) — secure cookies can't be set over http.
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
POSTGRES_DB=ssjd_cms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -hex 16)
DJANGO_SUPERUSER_EMAIL=admin@ssjd.coop
DJANGO_SUPERUSER_PASSWORD=$ADMIN_PW
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
MEDIA_STORAGE=local
PORTAL_URL=http://$IP
EOF
  echo "   generated .env (admin password: $ADMIN_PW)"
else
  echo "   .env already exists — keeping it."
fi

echo "▶ 6/6  Building & starting the stack (first build ~3-5 min)…"
sudo docker compose --env-file .env up -d --build

echo ""
echo "✅ Done."
echo "   Website : http://$IP:8080/"
echo "   Admin   : http://$IP:8080/admin/   (email: admin@ssjd.coop)"
echo "   API docs: http://$IP:8080/api/docs/"
echo "   Admin password is in $CMS_DIR/.env (DJANGO_SUPERUSER_PASSWORD)."
echo ""
echo "   NOTE: open TCP 8080 in the GCP firewall (see the instructions Claude gave)."
