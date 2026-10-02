package authctx

import (
	"github.com/golang-jwt/jwt/v5"
	"testing"
	"time"
)

func TestValidateJWTRequiresExpiration(t *testing.T) {
	secret := []byte("test-only-secret-minimum-32-characters")
	for _, tc := range []struct {
		name   string
		expiry *jwt.NumericDate
		valid  bool
	}{
		{"missing", nil, false},
		{"expired", jwt.NewNumericDate(time.Now().Add(-time.Minute)), false},
		{"valid", jwt.NewNumericDate(time.Now().Add(time.Minute)), true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			claims := Claims{Sub: "user", TenantID: "tenant", RegisteredClaims: jwt.RegisteredClaims{ExpiresAt: tc.expiry}}
			token, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(secret)
			if err != nil {
				t.Fatal(err)
			}
			_, err = ValidateJWT(token, secret)
			if (err == nil) != tc.valid {
				t.Fatalf("valid=%v, err=%v", tc.valid, err)
			}
		})
	}
}
