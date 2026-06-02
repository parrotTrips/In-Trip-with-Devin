FROM python:3.13-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==2.3.3

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install production dependencies only (no virtualenv inside container)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Cloud Run passes PORT env var; default to 8080
ENV PORT=8080

# Start server
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
