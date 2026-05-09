FROM node:22-slim

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
ENV NPM_CONFIG_FUND=false
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

COPY frontend/package*.json ./
RUN npm ci

COPY frontend ./

RUN npm run build

EXPOSE 3000

CMD npm run start -- --hostname 0.0.0.0
