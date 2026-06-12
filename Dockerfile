# Stage 1: Backend runtime for local Compose and backend-only deployments
FROM python:3.11-slim AS backend-runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies.
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Backend dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1 \
    pip install --no-cache-dir -r requirements.txt

# Copy Backend
COPY backend /app/

EXPOSE 8000

CMD ["python", "scripts/start_backend.py", "--host", "0.0.0.0", "--port", "8000"]

# Stage 2: Build Frontend
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

# Stage 3: Combined image (Python + Node.js)
FROM backend-runtime

# Runtime Node is copied from the frontend builder so apt does not install a
# distro Node package with noisy alternatives output.
COPY --from=frontend-builder /usr/local/bin/node /usr/local/bin/node

# Copy Frontend runtime artifacts
COPY --from=frontend-builder /app/.next /app/frontend/.next
COPY --from=frontend-builder /app/public /app/frontend/public
COPY --from=frontend-builder /app/node_modules /app/frontend/node_modules
COPY --from=frontend-builder /app/package.json /app/frontend/package.json
COPY --from=frontend-builder /app/next.config.ts /app/frontend/next.config.ts

# Startup is handled by scripts/docker_entrypoint.sh (copied with the backend in
# stage 1). It validates required configuration (DATABASE_URL,
# AUTH_SESSION_HMAC_SECRET, and a valid Fernet ENCRYPTION_KEY — never generated
# at runtime), then starts backend and frontend together and reports which
# service exits. Secrets must be supplied by the operator or orchestrator.
RUN chmod +x /app/scripts/docker_entrypoint.sh

# Create non-root user
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables for Frontend proxying inside the combined image
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV BACKEND_INTERNAL_URL=http://127.0.0.1:8000
ENV ALLOW_DOCKER_BACKEND_INTERNAL_URL=1

EXPOSE 3000 8000

CMD ["/app/scripts/docker_entrypoint.sh"]
