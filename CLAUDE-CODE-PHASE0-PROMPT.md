# Claude Code — Phase 0 Prompt

You are starting a production-grade Rice Mill ERP project.

Read `CLAUDE.md` and every file under `docs/` before making architectural decisions.

Your first task is **Phase 0: Foundation and Architecture**, not business-feature implementation.

## Instructions

1. Inspect the entire repository.
2. Determine whether this is a new or existing project.
3. Do not overwrite existing working code without understanding it.
4. Validate the documented domain model and identify contradictions.
5. Propose the final monorepo structure.
6. Propose frontend/backend/database boundaries.
7. Propose the initial PostgreSQL schema and migration plan.
8. Set up the development environment using the documented stack.
9. Set up Docker for local infrastructure.
10. Set up environment configuration and `.env.example`.
11. Set up linting, formatting, type checking, and test foundations.
12. Set up CI checks.
13. Establish health/readiness endpoints once the backend exists.
14. Create initial architectural documentation/decision records where needed.
15. Do not implement the Government Load, Milling, Rice, Dispatch, Claim, or Payment business modules yet.

## Technology

Frontend:
Next.js + React + TypeScript + Tailwind + shadcn/ui + TanStack Query + TanStack Table + React Hook Form + Zod.

Backend:
Python + FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic.

Data:
PostgreSQL + Redis + S3-compatible storage.

Testing:
Pytest + Vitest + Playwright.

Infrastructure:
Docker + GitHub Actions.

## Architecture

Use a modular monolith.

Browser
→ Next.js
→ FastAPI
→ PostgreSQL

Do not create microservices.

## Before Coding

Produce a short implementation plan based on the repository state.

If a material requirement is ambiguous, list it explicitly and choose the safest minimal Phase-1 interpretation only when it does not affect the core business model.

## Completion Report

At the end of Phase 0 report:

- repository assessment
- files created/changed
- architecture
- directory structure
- database strategy
- commands to run locally
- tests/checks executed
- unresolved decisions
- risks
- exact next recommended implementation step

Do not claim something is complete unless it was actually verified.
