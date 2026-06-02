FROM node:22-slim

WORKDIR /app

ENV NPM_CONFIG_UPDATE_NOTIFIER=false

COPY frontend/package*.json ./
ARG TARGETARCH
RUN npm ci --fetch-timeout=600000 --fetch-retries=5 \
    && if [ "$TARGETARCH" = "arm64" ] \
      && [ ! -f node_modules/lightningcss-linux-arm64-gnu/lightningcss.linux-arm64-gnu.node ]; then \
      npm install --fetch-timeout=600000 --fetch-retries=5 --no-save --package-lock=false lightningcss-linux-arm64-gnu@1.32.0; \
    fi

COPY frontend ./

ENV NEXT_TELEMETRY_DISABLED=1
# The browser client (frontend/src/lib/api-client.ts) uses an empty baseUrl
# and reaches the backend through the same-origin /api/* route handler.
# BACKEND_INTERNAL_URL is intentionally runtime-only so published images
# are not permanently wired to one deployment environment.
# NEXT_PUBLIC_API_URL is kept for backwards compatibility with callers that
# explicitly construct a base URL; new code should rely on the route handler.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
