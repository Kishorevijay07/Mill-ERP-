# Development Rules

## General

Write boring, clear, maintainable production code.

Do not optimize for code volume.

Do not create abstractions until they are justified.

Prefer explicit domain logic over magic.

## Backend

- Keep routes/controllers thin.
- Put business logic in services/domain modules.
- Keep persistence concerns separate.
- Use Pydantic schemas for API boundaries.
- Use SQLAlchemy 2.x patterns consistently.
- Use transactions deliberately.
- Make state transitions explicit.
- Validate authorization inside the backend.

## Frontend

- Keep page components compositional.
- Use feature-oriented modules.
- Keep server state in TanStack Query.
- Keep forms in React Hook Form + Zod.
- Do not duplicate backend business rules in the UI.
- UI calculations are for display; server calculations are authoritative.

## Database

- Every migration reviewed.
- Foreign keys required for relationships.
- Index common lookup paths.
- Avoid nullable fields unless null has semantic meaning.
- Avoid generic JSON blobs for core business data.
- JSON may be used for audit snapshots or genuinely flexible metadata.

## Inventory

Never mutate stock directly.

Use InventoryTransaction and business operations.

Stock-changing operations must be atomic.

## Documents

Store file metadata in PostgreSQL and files in object storage.

## Errors

Use safe, consistent errors.

Never show stack traces to users.

## Logging

Use structured logs.

Include useful identifiers such as:
- request ID
- user ID where appropriate
- business reference number

Never log secrets.

## Code Review Checklist

Before considering a feature complete:

- Is the business rule correct?
- Is authorization enforced?
- Is the transaction safe?
- Can duplicate requests cause corruption?
- Can concurrent requests overspend stock?
- Are validation errors clear?
- Are loading/error/empty states handled?
- Does mobile layout work?
- Are tests present?
- Is audit logging present where required?
- Is the change documented?
