#!/usr/bin/env bash
# ── HTTPS via Caddy for both SSJD apps on one VM ─────────────────────────────
# Fronts the main app (portal) and the website CMS with Caddy (auto Let's Encrypt).
# Run AFTER the GoDaddy DNS A-records point at this VM's IP:
#   curl -fsSL https://raw.githubusercontent.com/Anuj330/SSJD/feat/leadger_money_lead/deploy/caddy-setup.sh | bash
set -euo pipefail

DOMAIN="shreeshyamjankalyan.com"
APP_DIR="$HOME/SSJD"
CMS_DIR="$APP_DIR/SSJD-website-cms"
EMAIL="admin@${DOMAIN}"

# update-or-append KEY=VALUE in an env file
setenv() {
  local k="$1" v="$2" f="$3"
  if grep -q "^${k}=" "$f" 2>/dev/null; then
    sed -i "s|^${k}=.*|${k}=${v}|" "$f"
  else
    echo "${k}=${v}" >> "$f"
  fi
}

echo "▶ 1/6  Pulling latest code…"
git -C "$APP_DIR" pull -q || true

echo "▶ 2/6  Moving apps behind Caddy (bind to localhost)…"
# main app frontend: host :80 -> localhost:8090
sed -i 's|- "80:80"|- "127.0.0.1:8090:80"|' "$APP_DIR/docker-compose.prod.yml" || true
# CMS web: whatever host port -> localhost:8080
sed -i -E 's#- "([0-9.:]*):8000"#- "127.0.0.1:8080:8000"#' "$CMS_DIR/docker-compose.yml" || true

echo "▶ 3/6  Re-enabling HTTPS hardening on the CMS…"
CENV="$CMS_DIR/.env"
setenv ALLOWED_HOSTS "${DOMAIN},www.${DOMAIN}" "$CENV"
setenv CSRF_TRUSTED_ORIGINS "https://${DOMAIN},https://www.${DOMAIN}" "$CENV"
setenv CORS_ALLOWED_ORIGINS "https://${DOMAIN},https://www.${DOMAIN}" "$CENV"
setenv SESSION_COOKIE_SECURE "True" "$CENV"
setenv CSRF_COOKIE_SECURE "True" "$CENV"
setenv SECURE_HSTS_SECONDS "2592000" "$CENV"
setenv PORTAL_URL "https://portal.${DOMAIN}" "$CENV"

echo "▶ 4/6  Recreating app containers (frees port 80 for Caddy)…"
( cd "$APP_DIR" && sudo docker compose --env-file deploy.env -f docker-compose.prod.yml up -d )
( cd "$CMS_DIR" && sudo docker compose --env-file .env up -d --force-recreate )

echo "▶ 5/6  Installing Caddy…"
if ! command -v caddy >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl gnupg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y caddy
fi

echo "▶ 6/6  Writing Caddyfile + starting Caddy…"
sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
{
    email ${EMAIL}
}

${DOMAIN}, www.${DOMAIN} {
    reverse_proxy 127.0.0.1:8080
}

portal.${DOMAIN} {
    reverse_proxy 127.0.0.1:8090
}
EOF
sudo systemctl enable caddy >/dev/null 2>&1 || true
sudo systemctl restart caddy

echo ""
echo "✅ HTTPS setup complete (Caddy will fetch certs within ~30s if DNS is live)."
echo "   Website : https://${DOMAIN}   and   https://www.${DOMAIN}"
echo "   Portal  : https://portal.${DOMAIN}"
echo "   Check certs:  sudo journalctl -u caddy -n 40 --no-pager"
