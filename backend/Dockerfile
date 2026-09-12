# ==============================================================================
# Stage 1: Build & Dependencies
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Stage 2: Production Minimal Runtime
# ==============================================================================
FROM python:3.13-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user
RUN groupadd -g 10001 vault && \
    useradd -u 10001 -g vault -m -s /bin/bash vault

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/vault/.local
ENV PATH=/home/vault/.local/bin:$PATH
ENV PYTHONPATH=/app

# Create persistent storage directory with proper permissions
RUN mkdir -p /data/images && chown -R vault:vault /data/images /app

# Copy application source code
COPY --chown=vault:vault . /app

USER vault

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
