FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libopus0 git \
    && pip install --no-cache-dir \
        "doubaoime-asr @ git+https://github.com/starccy/doubaoime-asr.git" \
        "fastapi" "uvicorn" "python-multipart" "cryptography" \
    && apt-get purge -y git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY server.py .

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
