FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed the SQLite DB and pre-run the review-mining batch at build time so the
# container is demo-ready (falls back to keyword mining if no LLM is configured).
RUN python -m scripts.seed && python -m scripts.ingest_analysis

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
