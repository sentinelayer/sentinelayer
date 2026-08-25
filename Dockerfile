FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -e .
COPY src/ ./src/
COPY private/ ./private/
EXPOSE 8000
RUN python scripts/run_migrations.py
CMD ["uvicorn", "src.sentinelayer.api.main_full:app", "--host", "0.0.0.0", "--port", "8000"]
