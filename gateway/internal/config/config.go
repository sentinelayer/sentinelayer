package config

import (
	"os"
	"strconv"
)

type Config struct {
	Port        int
	UpstreamURL string
	RateLimit   int
	JWTSecret   string
}

func Load() *Config {
	port, _ := strconv.Atoi(getEnv("GATEWAY_PORT", "8080"))
	rateLimit, _ := strconv.Atoi(getEnv("RATE_LIMIT", "60"))
	return &Config{
		Port:        port,
		UpstreamURL: getEnv("UPSTREAM_URL", "http://localhost:8005"),
		RateLimit:   rateLimit,
		JWTSecret:   getEnv("JWT_SECRET", ""),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
