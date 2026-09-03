# Database Specification

## Database

PostgreSQL.

Use UUID primary keys for core entities where practical.

Use NUMERIC/Decimal for:
- monetary values
- weights/quantities requiring precision
- rates

Do not use floating point for money.

## Tables

### auth
- users
- roles
- user_roles

### master
- parties
- government_agencies
- mill_settings

### government
- allocations
- delivery_orders
- government_loads

### receiving
- weighments
- paddy_quality
- paddy_lots

### milling
- milling_batches
- milling_inputs
- rice_productions
- rice_production_outputs

### rice
- rice_quality
- rice_lots

### delivery
- dispatches
- dispatch_items
- delivery_receipts

### billing
- government_claims
- claim_lines
- payments

### inventory
- inventory_transactions

### system
- documents
- audit_logs

## Common Columns

Core tables should generally contain:
- id
- created_at
- updated_at
- created_by where appropriate
- updated_by where appropriate

Use soft deletion only where it has a clear business justification. Do not add soft delete everywhere automatically.

## Constraints

Use:
- foreign keys
- unique constraints
- check constraints
- not-null constraints
- indexes on foreign keys and common filters

Examples:
- quantity > 0 where applicable
- percentage fields constrained to valid ranges
- payment amount > 0
- claim amount >= 0
- bag count >= 0
- bag weight > 0

## Inventory

InventoryTransaction is the authoritative movement history.

Do not implement a UI that directly edits available stock.

For performance, cached/denormalized available quantities may exist, but they must be derived and protected by transactional business logic.

A stock-consuming transaction must lock/check available stock so concurrent requests cannot overspend inventory.

## Concurrency

Use database transactions for:
- accepting loads and creating stock
- milling consumption
- rice production stock creation
- dispatch stock deduction
- claim generation where duplicate claims must be prevented
- payment posting

Use appropriate row-level locking or equivalent PostgreSQL mechanisms where required.

## Migrations

Use Alembic.

Every schema change must have a migration.

Never edit an already-applied production migration to change historical meaning.

## Indexing

At minimum consider indexes for:
- reference numbers
- status
- created_at
- transaction dates
- government agency
- allocation_id
- delivery_order_id
- load_id
- paddy_lot_id
- milling_batch_id
- rice_lot_id
- dispatch_id
- claim_id

Avoid premature over-indexing.
