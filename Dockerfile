FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libopus0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY doubaoime_asr/ ./doubaoime_asr/

RUN pip install --no-cache-dir . "fastapi" "uvicorn" "python-multipart"

COPY server.py .

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
