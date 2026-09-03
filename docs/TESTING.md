# Testing Specification

## Test Pyramid

### Unit
Business calculations and pure domain logic.

### Integration
Database transactions, services, permissions, inventory rules.

### API
Endpoint validation, authorization, state transitions.

### E2E
Critical user journeys through the real browser.

## Required Business Tests

### Weighment
- gross > tare
- net calculation
- invalid weights rejected

### Paddy
- accepted load creates/permits lot
- rejected load cannot become usable stock
- consumption cannot exceed available

### Milling
- batch requires valid input
- multiple paddy lots can feed a batch
- completed batch cannot be arbitrarily edited

### Rice
- output linked to milling batch
- category quantities validated
- bag count calculation validated
- failed QC blocks dispatch

### Dispatch
- cannot dispatch unavailable stock
- cannot dispatch failed QC stock
- dispatch reduces stock exactly once
- duplicate dispatch action is prevented

### Delivery
- received quantity recorded
- shortage/excess calculated
- receipt cannot be duplicated incorrectly

### Claims
- only eligible deliveries can be claimed
- duplicate claiming prevented
- totals calculated server-side
- status transitions enforced

### Payments
- payment cannot exceed outstanding amount
- partial payment works
- full payment changes claim to PAID
- duplicate payment posting prevented

### Authorization
Test every sensitive operation for each Phase-1 role.

## Critical E2E Test

Run:

Login
→ Government Load
→ Weighment
→ Paddy QC
→ Accept
→ Paddy Lot
→ Milling Batch
→ Consume Paddy
→ Category 1
→ Category 2
→ Rice QC
→ Rice Lot
→ Dispatch
→ Delivery Receipt
→ Claim
→ PDF
→ Payment
→ Paid

This test is the primary release gate.

## Quality Gates

Before merging:
- formatter
- linter
- TypeScript type check
- backend type/lint checks as configured
- unit/integration tests
- relevant E2E tests

Before production:
- full test suite
- migration test from clean database
- backup/restore verification
- security review
- production configuration review
