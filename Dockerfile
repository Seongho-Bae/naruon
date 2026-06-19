FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies if any are needed for pgvector/psycopg2 and tiktoken on Python 3.14
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && export PATH="$HOME/.cargo/bin:$PATH" \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1 \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    pip install --no-cache-dir -r requirements.txt

COPY backend /app/

# Create a non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["python", "scripts/start_backend.py", "--host", "0.0.0.0", "--port", "8000"]
