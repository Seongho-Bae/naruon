FROM node:22-slim

WORKDIR /app

ENV NPM_CONFIG_UPDATE_NOTIFIER=false

COPY frontend/package*.json ./
ARG TARGETARCH
RUN npm ci \
    && if [ "$TARGETARCH" = "arm64" ] \
      && [ ! -f node_modules/lightningcss-linux-arm64-gnu/lightningcss.linux-arm64-gnu.node ]; then \
      npm install --no-save --package-lock=false lightningcss-linux-arm64-gnu@1.32.0; \
    fi

COPY frontend ./

ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
