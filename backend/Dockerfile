FROM python:3.11-slim

# fonts-dejavu-core provides the TrueType font used to render label text,
# libjpeg/zlib dev headers are needed by Pillow's wheel fallback build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir poetry==1.8.3
ENV PATH="/opt/poetry/bin:${PATH}"

WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml README.md ./
RUN poetry install --no-root --only main

# Copy application source
COPY app ./app

# Persistent data / label directories (also mounted as volumes via compose)
RUN mkdir -p /app/data /app/labels
ENV DATA_DIR=/app/data \
    LABELS_DIR=/app/labels

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
