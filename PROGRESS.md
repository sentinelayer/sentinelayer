# SentinelLayer - Status Aktual (2026-08-26)

## Yang Jalan
- JWT auth (env secret)
- BOLA/IDOR (logic benar, role-based belum diimplementasi)
- Rate limiting (Redis + in-memory, fallback buggy)
- WAF regex fallback (6 rules)
- Decision safety (kill switch, tanpa RBAC)
- Key rotation (Redis)
- 38/38 tests passing (belum diverifikasi ulang)

## Yang Perlu Diperbaiki
- Risk engine: global singleton → harus per-request
- Siap deploy: belum, auth masih hardcoded plaintext di beberapa tempat
- WAF: nama file masih "coraza_wrapper" padahal isinya regex fallback

## Status
- Masih dalam tahap perbaikan aktif
- Belum siap deploy production
