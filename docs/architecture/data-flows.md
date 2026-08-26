# Data Flows

## Request Flow
1. Client → Gateway (HTTPS)
2. Gateway → Normalize (internal)
3. Gateway → WAF (internal)
4. Gateway → Behavior (signal to engine)
5. Gateway → Risk (signal to engine)
6. Gateway → Decision (internal)
7. Gateway → Upstream (HTTPS)

## Control Flow
1. Admin → Control Plane (HTTPS)
2. Control Plane → Database (RLS)
3. Control Plane → Engine (config)
4. Control Plane → Dashboard (API)

## Observability Flow
1. Gateway → Prometheus (metrics)
2. Control Plane → Prometheus (metrics)
3. Engine → Prometheus (metrics)
4. All → Grafana (visualization)
