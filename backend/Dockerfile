# Build context is the REPO ROOT (see docker-compose.yml) so the image can
# include the shared engine package core/ alongside the backend. The image
# mirrors the repo layout (/repo/core + /repo/backend) so the sys.path
# bootstrap in app/__init__.py resolves identically in dev and in the container.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /repo/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ /repo/core/
COPY backend/ /repo/backend/

# Seed the SQLite DB and pre-run the review-mining batch at build time so the
# container is demo-ready (falls back to keyword mining if no LLM is configured).
RUN python -m scripts.seed && python -m scripts.ingest_analysis

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
