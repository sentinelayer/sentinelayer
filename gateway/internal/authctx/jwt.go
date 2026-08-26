package authctx

import (
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
    tokenString = strings.TrimPrefix(tokenString, "Bearer ")
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(t *jwt.Token) (interface{}, error) {
        return secret, nil
    })
    if err != nil {
        return nil, err
    }
    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }
    return nil, jwt.ErrSignatureInvalid
}
