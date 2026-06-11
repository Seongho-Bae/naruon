# Stage 1: Build Frontend
FROM node:22-slim AS frontend-builder
WORKDIR /app
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
RUN corepack enable pnpm
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml frontend/.pnpmfile.cjs ./
RUN pnpm install --frozen-lockfile
COPY frontend ./
# Pass dummy URL for build if needed
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
ENV POSTCSS_WORKERS=1
ENV DISABLE_POSTCSS_WORKERS=true
RUN pnpm run build

# Stage 2: Final Image (Python + Node.js)
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies. Runtime Node is copied from the frontend builder
# so apt does not install a distro Node package with noisy alternatives output.
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=frontend-builder /usr/local/bin/node /usr/local/bin/node

# Install Backend dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1 \
    pip install --no-cache-dir -r requirements.txt

# Copy Backend
COPY backend /app/

# Copy Frontend runtime artifacts
COPY --from=frontend-builder /app/.next /app/frontend/.next
COPY --from=frontend-builder /app/public /app/frontend/public
COPY --from=frontend-builder /app/node_modules /app/frontend/node_modules
COPY --from=frontend-builder /app/package.json /app/frontend/package.json
COPY --from=frontend-builder /app/next.config.ts /app/frontend/next.config.ts

# Create a startup script. DATABASE_URL and AUTH_SESSION_HMAC_SECRET must be
# supplied by the operator or orchestrator; do not generate runtime secrets here.
RUN echo '#!/bin/bash\n\
set -euo pipefail\n\
echo "Starting Naruon Backend and Frontend..."\n\
python scripts/bootstrap_db.py\n\
python scripts/start_backend.py --host 0.0.0.0 --port 8000 &\n\
BACKEND_PID=$!\n\
cd frontend && ./node_modules/.bin/next start --hostname 0.0.0.0 --port 3000 &\n\
FRONTEND_PID=$!\n\
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT\n\
wait -n "$BACKEND_PID" "$FRONTEND_PID"\n\
' > /app/start.sh && chmod +x /app/start.sh

# Create non-root user
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables for Frontend proxying inside the combined image
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV BACKEND_INTERNAL_URL=http://127.0.0.1:8000
ENV ALLOW_DOCKER_BACKEND_INTERNAL_URL=1

EXPOSE 3000 8000

CMD ["/app/start.sh"]
