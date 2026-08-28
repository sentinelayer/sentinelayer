# SentinelLayer on Cloudflare

This directory is the Cloudflare-native deployment entrypoint for SentinelLayer. It wraps the existing root `Dockerfile` in a Cloudflare Container and exposes the service through a Worker and a Durable Object container binding.

## Requirements

Cloudflare Containers is required for this deployment and must be enabled on a Workers Paid plan. The Cloudflare account must also have a Workers subdomain or a custom domain. The repository deployment workflow requires `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` GitHub Actions secrets.

The API token must be scoped only to the required account and resources, with permission to deploy Workers/Containers. Never commit the token or put it into `wrangler.jsonc`.

## Local validation

```bash
npm ci
npm run typecheck
npx wrangler deploy --dry-run --containers-rollout=none
```

A full local container build additionally requires Docker. The dry-run above validates the Worker bundle and binding shape without rolling out the container.

## Deployment

The workflow `.github/workflows/cloudflare-deploy.yml` deploys changes from `main` when the Cloudflare secret exists. Until the secret is configured, the workflow intentionally skips deployment and emits a warning. Railway remains untouched until the Cloudflare endpoint passes `/health`, `/api/v1/health`, `/status`, login, tenant isolation, and dashboard smoke checks.

## Current migration boundary

The existing container still starts the Go gateway, Python control plane, risk engine, behavior engine, and maintenance worker using the root Dockerfile. PostgreSQL and Redis remain external dependencies during the first Cloudflare Container rollout. A later phase can replace them with Hyperdrive/D1/Durable Objects/KV/Queues only after a schema and consistency review; this is not an automatic database migration.
