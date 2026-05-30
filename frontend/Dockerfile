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
# and reaches the backend through the same-origin /api/* rewrite defined in
# next.config.ts. The rewrite destination is read from BACKEND_INTERNAL_URL
# at build time (Next.js bakes rewrites into the build manifest). Render
# injects the value via fromService; docker-compose passes the in-network
# hostname together with ALLOW_INSECURE_BACKEND_INTERNAL_URL=1 because the
# private-range / http:// guards in next.config.ts otherwise fail closed.
# NEXT_PUBLIC_API_URL is kept for backwards compatibility with callers that
# explicitly construct a base URL; new code should rely on the rewrite.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ARG BACKEND_INTERNAL_URL
ENV BACKEND_INTERNAL_URL=$BACKEND_INTERNAL_URL
ARG ALLOW_INSECURE_BACKEND_INTERNAL_URL
ENV ALLOW_INSECURE_BACKEND_INTERNAL_URL=$ALLOW_INSECURE_BACKEND_INTERNAL_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
