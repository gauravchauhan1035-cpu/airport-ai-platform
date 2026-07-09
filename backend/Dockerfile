FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY entrypoint.sh .
# Need to copy alembic config and migrations for DB init
COPY alembic.ini .
COPY alembic ./alembic

RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

RUN mkdir -p /app/data/sqlite /app/data/faiss /app/data/pdfs /app/data/logs

# Security: Create and switch to non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
