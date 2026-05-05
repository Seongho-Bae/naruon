FROM node:22-slim

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend ./

ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
