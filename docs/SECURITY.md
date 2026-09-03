# Security Specification

## Authentication

Use secure password hashing.

Use secure session/token architecture suitable for a browser application.

Prefer HttpOnly, Secure, SameSite cookies for session credentials where appropriate.

Never store sensitive authentication tokens in localStorage unless there is a documented security reason.

## Authorization

Use RBAC with permissions.

Phase 1 roles:
- ADMIN
- OWNER
- STAFF

Design permissions so future roles can be introduced.

Example permissions:
- government.load.create
- government.load.view
- government.load.accept
- paddy.stock.view
- paddy.stock.adjust
- milling.batch.create
- rice.qc.approve
- dispatch.create
- dispatch.confirm
- billing.create
- billing.submit
- payment.record
- reports.view
- settings.manage

## Input Validation

Validate:
- request body
- path parameters
- query parameters
- file metadata
- quantities
- percentages
- identifiers

Backend validation is authoritative.

## File Upload Security

Validate:
- allowed MIME types
- file extension
- size
- content where feasible

Generate safe storage keys.

Never execute uploaded files.

Do not trust original filenames.

## Data Protection

Never log:
- passwords
- session secrets
- access tokens
- API keys

Use environment variables/secrets management.

## Audit

Audit important actions:
- create
- update
- accept/reject
- stock movement
- dispatch
- delivery confirmation
- claim submission/approval
- payment
- permission changes
- configuration changes

## Financial/Stock Integrity

Use transactions.

Prevent:
- negative stock
- duplicate claims
- overpayment
- duplicate payment posting
- invalid state transitions

## Web Security

Implement appropriate:
- CORS policy
- CSRF protection where applicable
- secure cookies
- security headers
- rate limiting
- request size limits

Do not use wildcard CORS in production.

## Operational Security

Provide:
- readiness endpoint
- liveness/health endpoint
- structured logs
- error monitoring
- database backup strategy
- secret rotation procedure documentation
