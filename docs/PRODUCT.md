# Product Specification — Rice Mill ERP Phase 1

## Product

Rice Mill ERP is a production-grade web application for a rice mill that receives Government-supplied paddy, processes it, produces rice in two categories, performs basic quality checks, dispatches rice to designated destinations, generates Government claims/bills, and tracks payments.

## Product Goal

Provide one simple system that answers:

- What Government paddy have we received?
- Where is it now?
- How much has been milled?
- How much rice has been produced?
- How much is available?
- What has been dispatched?
- What has been received by the destination?
- What Government claims have been submitted?
- How much has been paid?
- What remains outstanding?

## Phase 1 Scope

### Included

1. Authentication
2. Users and basic roles
3. Dashboard
4. Government allocations
5. Government delivery orders
6. Government loads/gate entry
7. Weighment
8. Paddy quality
9. Paddy lots
10. Paddy inventory
11. Milling batches
12. Milling inputs
13. Rice production
14. Two rice categories
15. Rice quality
16. Rice lots/bagging
17. Rice inventory
18. Dispatch
19. Delivery receipts
20. Government claims
21. Payment tracking
22. Basic reports
23. Printable documents
24. File attachments
25. Audit trail
26. Search

### Explicitly Deferred

Native mobile apps, advanced offline synchronization, AI, payroll, HR, CRM, complex accounting, IoT, biometric integration, automatic weighbridge integration, Government APIs, messaging automation, individual bag QR tracking, machine telemetry, predictive analytics, advanced warehouse management, multi-state rules, and advanced financial reporting.

## Primary Users

Phase 1:
- Admin
- Owner
- Staff

The permission model must be extensible so Staff can later be split into Gate Operator, Store Manager, Production Manager, QC Officer, Dispatch Operator, and Accounts.

## UX Principle

The application must be simple enough for real mill staff to use quickly.

Priorities:
1. correctness
2. speed
3. clarity
4. traceability
5. mobile usability
6. low training requirement

## Product Positioning

This is not a generic billing app.

It is a Rice Mill ERP with:
- Government stock workflow
- Milling operations
- Rice production
- Quality
- CMR/delivery workflow
- Government claims
- Payment tracking

Accounting and billing UX can be inspired by simple business apps, but the Government Paddy → Rice → Delivery → Claim chain is the core domain.
