# Deployment Specification

## Target Architecture

Internet
→ Cloudflare/CDN/DNS
→ reverse proxy / TLS
→ Next.js
→ FastAPI
→ PostgreSQL

Supporting:
- Redis
- S3-compatible object storage

## Containers

Use Docker for:
- frontend
- backend
- worker if background jobs are introduced
- local PostgreSQL/Redis development services

Production PostgreSQL should preferably be managed rather than self-hosted unless there is a specific infrastructure reason.

## Environments

At minimum:
- development
- staging
- production

Never use production credentials locally.

## Configuration

Use environment variables.

Maintain `.env.example`.

Required configuration should be validated at application startup.

## CI/CD

Pipeline should:
1. install dependencies
2. lint
3. type check
4. test
5. build
6. run migration checks
7. build production images
8. deploy after approval where appropriate
9. run health checks

## Database

Use automated backups.

Document:
- backup frequency
- retention
- restore procedure
- migration procedure

## Observability

Provide:
- application logs
- error monitoring
- request correlation IDs where useful
- health endpoint
- readiness endpoint
- database connectivity monitoring

## Production Readiness

Before release verify:
- HTTPS
- secure cookies
- CORS
- rate limiting
- backups
- secrets
- database migrations
- storage permissions
- error handling
- logging
- monitoring
- rollback plan
