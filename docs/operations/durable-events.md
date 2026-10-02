# Durable tenant event stream

The database is the event source for all API workers. WebSocket clients no
longer broadcast arbitrary messages to other subscribers. Event ingestion goes
through authenticated `POST /api/v1/events`; policy mutations append
server-origin `policy.changed` events in the same transaction as policy state.
Tenant callers cannot forge `policy.*` events or the `control-plane` source.

## Protocol

- Connect to `/api/v1/events-ws/stream` with a bearer header, or the existing
  query-token mechanism. Avoid query tokens where access logs retain URLs.
- Omit `after` to start at the latest committed tenant cursor. Use `after=0`
  to replay retained history, or a previously persisted cursor to resume.
- The first message is `{"type":"stream.ready","cursor":0,"latest":0}`.
  Subsequent messages are `{"type":"event","cursor":1,"event":{...}}`.
  Persist the cursor only after processing the event. Duplicate replay is
  expected after disconnects; deduplicate by event ID/cursor.
- Text `ping` returns `{"type":"pong","cursor":...}`. Other client messages
  close with 1008. A malformed/future cursor also closes with 1008.
- Session revocation/expiry is checked during polling, before sending each
  event and on incoming messages. Invalidated sessions close with 1008.
- Database failure or a five-second send timeout closes with 1013. Reconnect
  with the last processed cursor. HTTP history supports `GET /api/v1/events?after=N`
  in ascending cursor order, with a maximum page of 500.

## Ordering and durability

Each tenant has a database counter. Incrementing it locks that tenant's row
until the event/domain transaction commits. A later cursor therefore cannot
commit ahead of an earlier in-flight event. Rollback undoes both the event and
counter increment. Uncommitted events are never delivered.

Runtime database grants permit event SELECT/INSERT, not UPDATE/DELETE. All
tenant counter/event reads have explicit tenant filters/context and PostgreSQL
RLS. Each socket polls independently, so workers share neither a socket manager
nor an in-memory queue. A restarted worker can replay committed history.

## Deployment and limits

Migration `0027` adds/backfills cursors, creates the counter table and enables
its RLS policy. Back up first; pause old event writers during the migration,
which locks the event table. Migrate/provision roles in the separate privileged
job before starting the new API image. Never enable production startup migration
or expose migration credentials to runtime workers.

Polling is every second, with batches of 100 and bounded socket sends. This
trades database load for simple durable delivery; measure connection count,
database latency and replay lag before a large deployment. This is reconnect
replay, not a consumer-group or exactly-once acknowledgement protocol. The
browser/client must store its cursor. Durability follows PostgreSQL commit and
the deployment's backup/PITR settings; it is not evidence of full disaster recovery.

Tests cover transactional rollback, isolated worker factories, tenant filtering,
replay, client-injection rejection and revoked sessions. The restricted-production
PostgreSQL CI test additionally starts two real API processes, ingests on one,
subscribes on the other, terminates a process, replays and verifies logout closure.
