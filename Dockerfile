FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY waf ./waf
COPY private ./private

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

EXPOSE 8000

CMD ["uvicorn", "src.sentinelayer.api.main_full:app", "--host", "0.0.0.0", "--port", "8000"]
