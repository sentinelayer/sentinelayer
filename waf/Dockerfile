FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o waf .

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/waf .
EXPOSE 8080
CMD ["./waf"]
