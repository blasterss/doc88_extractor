FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOC88_DATA_DIR=/app/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY packaging/install_tools.py ./packaging/install_tools.py

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev \
    && .venv/bin/python packaging/install_tools.py

RUN mkdir -p /app/data

EXPOSE 8000
CMD [".venv/bin/uvicorn", "doc88_extractor.presentation.web:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
