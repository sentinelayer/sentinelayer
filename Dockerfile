FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir fastapi uvicorn pydantic python-jose redis sqlalchemy psycopg2-binary

# Copy application
COPY src/ ./src/
COPY private/ ./private/

EXPOSE 8000

CMD ["uvicorn", "src.sentinelayer.api.main_full:app", "--host", "0.0.0.0", "--port", "8000"]
