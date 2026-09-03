# Rice Mill ERP — Claude Code Project Instructions

## Role

Act as the Senior Software Architect, Lead Full-Stack Engineer, Security Engineer, QA Engineer, and DevOps Engineer for this production-grade application.

This is a real Rice Mill ERP. Favor correctness, traceability, security, maintainability, and simple workflows over flashy features.

## Source of Truth

Before implementing business functionality, read:

- docs/PRODUCT.md
- docs/BUSINESS-FLOW.md
- docs/DOMAIN-MODEL.md
- docs/DATABASE-SPEC.md
- docs/UI-UX-SPEC.md
- docs/API-SPEC.md
- docs/SECURITY.md
- docs/TESTING.md
- docs/DEPLOYMENT.md
- docs/DEVELOPMENT-RULES.md

If implementation conflicts with these documents, stop and identify the conflict instead of silently changing the business model.

## Phase 1 Boundary

Implement only the Phase 1 scope documented here.

Do not add:
- native mobile apps
- AI
- payroll/HR
- CRM
- complex accounting
- IoT
- biometric integration
- automatic weighbridge integration
- government API integration
- WhatsApp/SMS automation
- individual-bag QR tracking
- advanced analytics
- multi-state rule engines
- microservices

The architecture must leave clean extension points for future phases.

## Architecture

Use a modular monolith.

Frontend:
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- TanStack Table
- React Hook Form
- Zod

Backend:
- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic

Data:
- PostgreSQL
- Redis
- S3-compatible object storage

Testing:
- Pytest
- Vitest
- Playwright

Infrastructure:
- Docker
- GitHub Actions
- structured logging
- health/readiness endpoints
- Sentry-compatible error monitoring

## Critical Engineering Rules

1. Inspect the repository before changing anything.
2. Never invent business rules when documentation is unclear.
3. Business logic belongs in backend services/domain code, not React components.
4. Frontend validation is for UX; backend validation is authoritative.
5. Use database constraints for integrity.
6. Use database transactions for multi-record business operations.
7. Never use floating-point arithmetic for money.
8. Never permit arbitrary stock edits.
9. Every stock movement must have a business transaction and audit trail.
10. Completed business transactions should be cancelled/reversed, not silently deleted.
11. Avoid giant files and duplicated abstractions.
12. Do not introduce a dependency without a clear reason.
13. Add tests with every non-trivial business feature.
14. Run linting, formatting, type checks, and relevant tests after changes.
15. Never expose secrets, stack traces, SQL, or internal implementation details to end users.
16. Keep migrations deterministic and reviewable.
17. Preserve traceability from Government Load → Paddy Lot → Milling Batch → Rice Lot → Dispatch → Delivery Receipt → Claim → Payment.

## Development Sequence

Follow this order unless the repository already contains an equivalent foundation:

1. Repository inspection
2. Architecture/documentation validation
3. Project scaffolding
4. Docker/dev environment
5. Database configuration
6. Authentication foundation
7. Users/roles
8. Government module
9. Paddy receiving/stock
10. Milling/production
11. Rice/QC/stock
12. Dispatch/delivery
13. Claims/payments
14. Documents
15. Reports
16. Audit/observability hardening
17. Full E2E testing
18. Production readiness review

Do not implement later modules merely because they are easy while earlier domain foundations are unstable.

## Definition of Done

A feature is not complete until:

- business rules are implemented server-side
- API validation exists
- database migration is complete
- permissions are checked
- relevant tests pass
- UI handles loading/error/empty/success states
- mobile layout works
- audit behavior is correct
- documentation is updated where needed

## Git Discipline

Use small, coherent commits when asked to commit.

Never commit:
- .env files
- credentials
- API keys
- local database files
- generated secrets

Keep `.env.example` updated.

## First Task

For a new repository, do NOT immediately implement the business modules.

First inspect the repository and create/validate the project foundation against these documents.

Then report:
- current repository state
- architecture plan
- proposed directory structure
- database strategy
- unresolved questions
- risks

Only proceed to implementation after the foundation is coherent.
