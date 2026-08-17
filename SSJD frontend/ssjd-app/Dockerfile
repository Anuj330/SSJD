# ── SSJD Frontend (production) ──────────────────────────────────────────────
# Stage 1: build the Vite/React app.
# Stage 2: serve the static bundle with nginx and proxy API calls to the backend.

FROM node:20-alpine AS build

WORKDIR /app

# Install deps (use lockfile when present for reproducible builds).
COPY package*.json ./
RUN npm ci

COPY . .

# Leave VITE_API_BASE_URL empty so axios uses relative URLs (/api, /auth, ...)
# which nginx then proxies to the backend. Override at build time if the API
# is served from a different origin.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# ── Serve ───────────────────────────────────────────────────────────────────
FROM nginx:alpine

# Backend origin that nginx proxies API paths to. Overridable at runtime.
ENV BACKEND_URL=http://backend:8000
# Only substitute BACKEND_URL in the template, leaving nginx's own $vars intact.
ENV NGINX_ENVSUBST_FILTER=BACKEND_URL

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
