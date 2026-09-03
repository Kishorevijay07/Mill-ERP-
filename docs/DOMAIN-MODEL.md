# Domain Model

## Core Entities

### User
Authentication identity.

### Role
Authorization grouping.

### Party
Generic organization/person record for business relationships.

### GovernmentAgency
Government organization associated with allocations, orders, claims, or destinations.

### Allocation
Government-assigned paddy quantity.

### DeliveryOrder
Government instruction associated with an allocation.

### GovernmentLoad
Physical government paddy load arriving at the mill.

### Weighment
Gross, tare, and calculated net weight for a load.

### PaddyQuality
Quality inspection associated with a load.

### PaddyLot
Traceable paddy stock unit created from an accepted load.

### MillingBatch
Production event that consumes one or more paddy lots.

### MillingInput
Join entity between milling batch and paddy lot.

### RiceProduction
Production record belonging to a milling batch.

### RiceProductionOutput
Output of a production record. Supports two configurable categories.

### RiceQuality
QC record for a rice production output.

### RiceLot
Traceable rice stock lot created from an accepted production output.

### Dispatch
Shipment leaving the mill.

### DispatchItem
Join entity between dispatch and rice lots.

### DeliveryReceipt
Destination confirmation of dispatched goods.

### GovernmentClaim
Financial claim generated from eligible delivery transactions.

### ClaimLine
Individual charge line inside a claim.

### Payment
Payment against a Government claim.

### InventoryTransaction
Immutable-style stock movement record representing why inventory changed.

### Document
Metadata for an uploaded file.

### AuditLog
History of important system mutations.

## Relationships

Allocation 1:N DeliveryOrder

DeliveryOrder 1:N GovernmentLoad

GovernmentLoad 1:1 or 1:N Weighment records depending on weighment design; the application must define which weighment is the authoritative final weighment.

GovernmentLoad 1:1 PaddyQuality for Phase 1.

GovernmentLoad 1:N PaddyLot only if operationally required; otherwise prefer 1:1 for simplicity.

MillingBatch N:M PaddyLot through MillingInput.

MillingBatch 1:N RiceProduction.

RiceProduction 1:N RiceProductionOutput.

RiceProductionOutput 1:1 RiceQuality.

RiceProductionOutput 1:N RiceLot only if split lots are required; otherwise prefer 1:1.

Dispatch N:M RiceLot through DispatchItem.

Dispatch 1:1 or 1:N DeliveryReceipt depending on partial receipt requirements. Phase 1 should support one final receipt plus shortage/excess fields unless real operations require partial receipts.

GovernmentClaim 1:N ClaimLine.

GovernmentClaim 1:N Payment to support partial payments.

InventoryTransaction references the affected lot and source business transaction.

Documents use polymorphic entity references only where necessary and must be validated server-side.

## Human-Readable References

Use separate human-readable identifiers such as:

AL-000001
DO-000001
LD-000001
PL-000001
MB-000001
RP-000001
RL-000001
DEL-000001
REC-000001
CLM-000001
PAY-000001

These are not database primary keys.

## Domain Principle

IDs identify records.

Business reference numbers identify transactions to users.

Relationships preserve traceability.

InventoryTransaction preserves movement history.

AuditLog preserves mutation history.
