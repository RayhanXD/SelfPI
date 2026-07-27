# syntax=docker/dockerfile:1

# --- build stage ---
FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
COPY backend/api ./api
COPY backend/db ./db
COPY backend/diff ./diff
COPY backend/watcher ./watcher
COPY backend/scanner ./scanner
COPY backend/patcher ./patcher
COPY backend/languages ./languages
COPY backend/llm ./llm
COPY backend/pipeline ./pipeline
COPY backend/detector ./detector

RUN pip install --no-cache-dir --prefix=/install .

# --- runtime ---
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin selfpi

WORKDIR /app

COPY --from=builder /install /usr/local
COPY backend/api ./api
COPY backend/db ./db
COPY backend/diff ./diff
COPY backend/watcher ./watcher
COPY backend/scanner ./scanner
COPY backend/patcher ./patcher
COPY backend/languages ./languages
COPY backend/llm ./llm
COPY backend/pipeline ./pipeline
COPY backend/detector ./detector
COPY backend/pyproject.toml ./

RUN mkdir -p /app/.cache/checkouts \
    && chown -R selfpi:selfpi /app

USER selfpi

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=production \
    PORT=8000 \
    CHECKOUT_ROOT=/app/.cache/checkouts \
    INCLUDE_DEMO_APIS=false

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=3)"

# Clones under CHECKOUT_ROOT are ephemeral — re-cloned on connect/detect after restart.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
