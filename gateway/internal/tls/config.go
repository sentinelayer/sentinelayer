package tls

import (
    "crypto/tls"
)

func GetTLSConfig() *tls.Config {
    return &tls.Config{
        MinVersion: tls.VersionTLS13,
        CurvePreferences: []tls.CurveID{
            tls.X25519,
            tls.CurveP256,
            tls.CurveP384,
        },
        CipherSuites: []uint16{
            tls.TLS_AES_256_GCM_SHA384,
            tls.TLS_CHACHA20_POLY1305_SHA256,
            tls.TLS_AES_128_GCM_SHA256,
        },
    }
}
