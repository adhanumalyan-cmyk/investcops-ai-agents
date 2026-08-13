FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY ai-agents/ /app/ai-agents/

WORKDIR /app/backend

ENV DATABASE_URL=sqlite:////app/data/investcops.db
ENV LOCAL_STORAGE_DIR=/app/data/evidence
ENV LOG_LEVEL=INFO

RUN mkdir -p /app/data /app/data/evidence

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]