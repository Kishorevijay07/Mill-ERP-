# Business Flow

## End-to-End Flow

Government Allocation
→ Delivery Order
→ Government Load
→ Weighment
→ Paddy Quality
→ Paddy Acceptance
→ Paddy Lot
→ Paddy Inventory
→ Milling Batch
→ Milling Input
→ Rice Production
→ Rice Quality
→ Rice Lot
→ Rice Inventory
→ Dispatch
→ Delivery Receipt
→ Government Claim
→ Payment

## Traceability

Forward:

Government Allocation
→ Delivery Order
→ Load
→ Paddy Lot
→ Milling Batch
→ Rice Lot
→ Dispatch
→ Delivery Receipt
→ Claim
→ Payment

Backward:

Payment
→ Claim
→ Delivery Receipt
→ Dispatch
→ Rice Lot
→ Milling Batch
→ Paddy Lot
→ Government Load
→ Delivery Order
→ Allocation

## Government Load States

DRAFT
→ ARRIVED
→ WEIGHED
→ QC_PENDING
→ ACCEPTED

Alternative:
QC_PENDING → REJECTED

## Milling Batch States

DRAFT
→ IN_PROGRESS
→ COMPLETED

## Rice QC States

PENDING
→ PASSED

Alternative:
PENDING → FAILED

## Dispatch States

DRAFT
→ PREPARED
→ DISPATCHED
→ DELIVERED

## Claim States

DRAFT
→ SUBMITTED
→ APPROVED
→ PARTIALLY_PAID
→ PAID

## Core Rules

1. A load cannot be accepted without valid weighment.
2. A usable Paddy Lot can only be created from an accepted load.
3. Paddy consumption cannot exceed available quantity.
4. A milling batch cannot consume unavailable stock.
5. Rice output must be associated with a milling batch.
6. Rice that fails QC cannot be dispatched.
7. Dispatch cannot exceed available rice stock.
8. Delivery receipt records actual destination receipt.
9. Claims should be generated from completed/eligible deliveries.
10. Payment cannot exceed outstanding claim balance.
11. Stock changes must originate from transactions.
12. Important completed records are not silently deleted.
13. All important mutations are auditable.

## Stock Movement Principles

Paddy:
- ACCEPTED LOAD → positive stock movement
- MILLING INPUT → negative stock movement

Rice:
- PRODUCTION OUTPUT → positive stock movement
- DISPATCH → negative stock movement

## Critical E2E Scenario

Login
→ Create Government Load
→ Record Weighment
→ Record Paddy QC
→ Accept Load
→ Create Paddy Lot
→ Create Milling Batch
→ Consume Paddy
→ Produce Category 1 and Category 2
→ Rice QC
→ Create Rice Lots
→ Dispatch
→ Delivery Receipt
→ Government Claim
→ Generate PDF
→ Record Payment
→ Claim becomes Paid
