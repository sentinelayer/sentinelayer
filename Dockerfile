# Gateway (Go)
FROM golang:1.22-alpine AS gateway-builder
WORKDIR /gateway
COPY gateway/go.mod gateway/go.sum ./
RUN go mod download
COPY gateway/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway ./cmd/gateway

# Control Plane / Risk (Python)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -m -u 1000 sentinel

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY control_plane ./control_plane
COPY engine ./engine
COPY alembic.ini ./

COPY --from=gateway-builder /gateway/gateway /usr/local/bin/gateway

RUN chown -R sentinel:sentinel /app
USER sentinel

ENV PYTHONPATH=/app

EXPOSE 8005 8090

CMD ["sh", "-c", "uvicorn control_plane.app.main:app --host 0.0.0.0 --port 8005"]
