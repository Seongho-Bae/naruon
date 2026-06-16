FROM node:22-slim

ARG OCI_IMAGE_CREATED=""
ARG OCI_IMAGE_AUTHORS="Seongho Bae"
ARG OCI_IMAGE_URL="https://github.com/Seongho-Bae/naruon"
ARG OCI_IMAGE_DOCUMENTATION="https://github.com/Seongho-Bae/naruon#readme"
ARG OCI_IMAGE_SOURCE="https://github.com/Seongho-Bae/naruon"
ARG OCI_IMAGE_VERSION="0.14.3"
ARG OCI_IMAGE_REVISION=""
ARG OCI_IMAGE_VENDOR="Seongho-Bae"
ARG OCI_IMAGE_LICENSES="LicenseRef-Naruon-Proprietary"
ARG OCI_IMAGE_REF_NAME=""
ARG OCI_IMAGE_TITLE="naruon frontend"
ARG OCI_IMAGE_DESCRIPTION="Naruon Next.js frontend runtime image"
ARG OCI_IMAGE_BASE_DIGEST=""
ARG OCI_IMAGE_BASE_NAME="docker.io/library/node:22-slim"

LABEL org.opencontainers.image.created="${OCI_IMAGE_CREATED}" \
      org.opencontainers.image.authors="${OCI_IMAGE_AUTHORS}" \
      org.opencontainers.image.url="${OCI_IMAGE_URL}" \
      org.opencontainers.image.documentation="${OCI_IMAGE_DOCUMENTATION}" \
      org.opencontainers.image.source="${OCI_IMAGE_SOURCE}" \
      org.opencontainers.image.version="${OCI_IMAGE_VERSION}" \
      org.opencontainers.image.revision="${OCI_IMAGE_REVISION}" \
      org.opencontainers.image.vendor="${OCI_IMAGE_VENDOR}" \
      org.opencontainers.image.licenses="${OCI_IMAGE_LICENSES}" \
      org.opencontainers.image.ref.name="${OCI_IMAGE_REF_NAME}" \
      org.opencontainers.image.title="${OCI_IMAGE_TITLE}" \
      org.opencontainers.image.description="${OCI_IMAGE_DESCRIPTION}" \
      org.opencontainers.image.base.digest="${OCI_IMAGE_BASE_DIGEST}" \
      org.opencontainers.image.base.name="${OCI_IMAGE_BASE_NAME}"

WORKDIR /app

ENV NPM_CONFIG_UPDATE_NOTIFIER=false
RUN corepack enable pnpm

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml frontend/.pnpmfile.cjs ./
ARG TARGETARCH
RUN pnpm install --frozen-lockfile \
    && if [ "$TARGETARCH" = "arm64" ] \
      && [ ! -f node_modules/lightningcss-linux-arm64-gnu/lightningcss.linux-arm64-gnu.node ]; then \
      pnpm install lightningcss-linux-arm64-gnu@1.32.0; \
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

ENV POSTCSS_WORKERS=1
ENV DISABLE_POSTCSS_WORKERS=true

RUN pnpm run build

RUN chown -R node:node /app
USER node

EXPOSE 3000

# Render injects $PORT at runtime
CMD sh -c "exec ./node_modules/.bin/next start --hostname 0.0.0.0 --port ${PORT:-3000}"
