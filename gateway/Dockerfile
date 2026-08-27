FROM golang:1.25-alpine AS builder
WORKDIR /src
RUN apk add --no-cache git
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go mod tidy && CGO_ENABLED=0 GOOS=linux go build -o /gateway ./cmd/gateway

FROM alpine:3.20
RUN apk add --no-cache ca-certificates \
    && addgroup -S gateway \
    && adduser -S -G gateway gateway
COPY --from=builder /gateway /usr/local/bin/gateway
USER gateway
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/gateway"]
