FROM python:3.13-slim AS base
WORKDIR /app

FROM base AS builder
RUN pip install --no-cache-dir hatch
COPY pyproject.toml .
COPY bot/ bot/
RUN hatch build -t wheel

FROM base AS runtime
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Copy default config (override with volume mount)
COPY config.yaml.example /app/config.yaml

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "bot"]
