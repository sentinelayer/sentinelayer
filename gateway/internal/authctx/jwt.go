package authctx

import (
	"errors"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

type Claims struct {
	Sub      string `json:"sub"`
	Email    string `json:"email"`
	TenantID string `json:"tenant_id"`
	IsAdmin  bool   `json:"is_admin"`
	jwt.RegisteredClaims
}

func ValidateJWT(tokenString string, secret []byte) (*Claims, error) {
	if len(secret) < 32 {
		return nil, errors.New("JWT secret must be at least 32 bytes")
	}
	tokenString = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(tokenString), "Bearer "))
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(t *jwt.Token) (interface{}, error) {
		if t.Method != jwt.SigningMethodHS256 {
			return nil, errors.New("unexpected JWT signing algorithm")
		}
		return secret, nil
	})
	if err != nil {
		return nil, err
	}
	if claims, ok := token.Claims.(*Claims); ok && token.Valid && claims.Sub != "" && claims.TenantID != "" {
		return claims, nil
	}
	return nil, jwt.ErrSignatureInvalid
}
