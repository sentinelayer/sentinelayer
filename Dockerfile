FROM python:3.11-slim

RUN useradd -m -u 1000 sentinel
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY waf ./waf
COPY private ./private
COPY frontend ./frontend

RUN chown -R sentinel:sentinel /app
USER sentinel

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.sentinelayer.api.main_full:app", "--host", "0.0.0.0", "--port", "8000"]
