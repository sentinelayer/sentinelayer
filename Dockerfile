FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

RUN mkdir -p private/evidence/requirements private/keys
RUN echo '{"secrets": {}}' > private/secrets.json
RUN echo '{"artifacts": {}}' > private/manifest.json

ENV PYTHONPATH=/app/src

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn sentinelayer.api.main_full:app --host 0.0.0.0 --port $PORT"]
