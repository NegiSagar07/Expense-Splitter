# ==============================================================
# Expense Splitter — Backend Dockerfile
# Multi-stage build: lean production image
# ==============================================================

# ── Stage 1: dependency builder ────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools only in this stage (not carried to runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────
FROM python:3.11-slim AS runtime

# Security: run as non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Render injects PORT at runtime; default 8000 for local use
ENV PORT=8000

# Switch to non-root user
USER appuser

# Expose the port (informational; Render overrides via $PORT)
EXPOSE ${PORT}

# Start command: run Alembic migrations then launch Uvicorn on $PORT
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
