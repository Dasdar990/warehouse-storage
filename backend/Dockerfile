FROM python:3.11-slim

# Copy uv pre-built binary directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# fonts-dejavu-core provides the TrueType font used to render label text
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Environment variables to optimize Python & uv behavior in Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --frozen --no-install-project --no-dev

# Place the virtual environment's executables directly in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY app ./app
COPY assets ./assets

# Persistent data / label directories (also mounted as volumes via compose)
RUN mkdir -p /app/data /app/labels
ENV DATA_DIR=/app/data \
    LABELS_DIR=/app/labels \
    ASSETS_DIR=/app/assets

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]