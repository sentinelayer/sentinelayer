FROM node:22-alpine AS dashboard-builder
WORKDIR /dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci --ignore-scripts
COPY dashboard/ ./
RUN npm run build

FROM golang:1.25-alpine AS gateway-builder
WORKDIR /gateway
COPY gateway/go.mod gateway/go.sum ./
RUN go mod download
COPY gateway/ .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway ./cmd/gateway

FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -m -u 1000 sentinel
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY control_plane ./control_plane
COPY engine ./engine
COPY security ./security
COPY waf ./waf
COPY scripts ./scripts
COPY --from=dashboard-builder /dashboard/dist ./dashboard/dist
COPY alembic.ini ./
RUN python scripts/generate_runtime_provenance.py
COPY --from=gateway-builder /gateway/gateway /usr/local/bin/gateway
RUN chmod 0555 /app/scripts/start_single_service.sh /usr/local/bin/gateway
RUN chown -R sentinel:sentinel /app
USER sentinel
ENV PYTHONPATH=/app
ENV CRS_RULES_DIR=/app/waf/rules
EXPOSE 8080 8005 8090
ENTRYPOINT ["/app/scripts/start_single_service.sh"]
