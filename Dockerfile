FROM python:3.11-slim

RUN useradd -m -u 1000 sentinel
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY control_plane ./control_plane
COPY engine ./engine

RUN chown -R sentinel:sentinel /app
USER sentinel

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

EXPOSE 8005

CMD ["uvicorn", "control_plane.app.main:app", "--host", "0.0.0.0", "--port", "8005"]
