# ==========================================
# Multi-Stage Production Dockerfile
# Stage 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml LICENSE README.md* ./
COPY src ./src

RUN pip install --no-cache-dir build \
    && python -m build --wheel

# ==========================================
# Stage 2: Final Production Runtime
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATABASE_URL=sqlite:////app/data/experiments.db
ENV LOG_LEVEL=INFO

# Security best practice: Run as non-privileged non-root user
RUN useradd --create-home --uid 1000 --shell /bin/bash appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Install compiled application wheel from builder stage
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm -rf /tmp/*.whl

USER appuser

EXPOSE 8000

# Container health monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["experiment-registry", "--host", "0.0.0.0", "--port", "8000"]
