FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for better caching)
COPY pyproject.toml requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir fastapi uvicorn pydantic python-jose redis sqlalchemy psycopg2-binary

# Copy application code
COPY src/ ./src/
COPY private/ ./private/

EXPOSE 8000

CMD ["uvicorn", "src.sentinelayer.api.main_full:app", "--host", "0.0.0.0", "--port", "8000"]
