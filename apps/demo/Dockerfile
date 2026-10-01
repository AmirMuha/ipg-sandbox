FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
# psycopg2-binary + the `postgresql+psycopg2://` scheme: bare `postgresql://` resolves to
# psycopg3 under SQLAlchemy 2.x, and without either the container died at import with
# `ModuleNotFoundError: No module named 'psycopg'` and the demo profile never came up.
RUN pip install --no-cache-dir fastapi uvicorn httpx sqlalchemy psycopg2-binary

COPY src /app/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
