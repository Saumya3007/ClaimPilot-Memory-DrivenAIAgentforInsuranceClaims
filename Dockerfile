FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml uv.lock /app/
# Syncing with --frozen to use the CPU torch index we just added
RUN uv sync --frozen --no-dev --no-cache

COPY . /app

EXPOSE 8000 8501

CMD ["uv", "run", "python", "main.py"]
