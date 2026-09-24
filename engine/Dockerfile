FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/
RUN pip install --no-cache-dir .

EXPOSE 8080
# Migrate then serve: the app queries tables at startup, so `alembic upgrade head` must run
# first — otherwise a fresh `docker compose up` dies on "relation ... does not exist".
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.api.app:app --host 0.0.0.0 --port 8080"]
