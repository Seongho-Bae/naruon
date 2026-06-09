# Stage 1: Build Frontend
FROM node:22-slim AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
# Pass dummy URL for build if needed
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Final Image (Python + Node.js)
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies & Node.js
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

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

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Starting Naruon Backend and Frontend..."\n\
python scripts/bootstrap_db.py\n\
python scripts/start_backend.py --host 0.0.0.0 --port 8000 &\n\
BACKEND_PID=$!\n\
cd frontend && npm run start -- --hostname 0.0.0.0 --port 3000 &\n\
FRONTEND_PID=$!\n\
wait -n\n\
exit $?\n\
' > /app/start.sh && chmod +x /app/start.sh

# Create non-root user
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables for Backend and Frontend
ENV DATABASE_URL=sqlite+aiosqlite:///./naruon_standalone.db
ENV AUTH_SESSION_HMAC_SECRET=local-dev-dummy-key-of-32-bytes-min-length-1234
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV BACKEND_INTERNAL_URL=http://127.0.0.1:8000
ENV ALLOW_DOCKER_BACKEND_INTERNAL_URL=1

EXPOSE 3000 8000

CMD ["/app/start.sh"]
