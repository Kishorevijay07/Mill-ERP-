# UI/UX Specification

## General

Responsive web application. No native mobile app in Phase 1.

Desktop:
- sidebar navigation
- data tables
- keyboard-friendly workflows
- clear action hierarchy

Mobile:
- compact navigation
- large touch targets
- single-column forms
- responsive cards
- horizontally scrollable tables only when unavoidable
- numeric keyboard-friendly inputs
- sticky primary action where appropriate

## Navigation

Dashboard

Government
- Allocations
- Delivery Orders
- Loads

Paddy
- Stock
- Quality

Milling
- Batches
- Production

Rice
- Stock
- Quality

Delivery
- Dispatch
- Receipts

Billing
- Claims
- Payments

Reports

Settings

## Screens

### Login
Username/email, password, login, forgot-password placeholder if supported.

### Dashboard
KPIs:
- government paddy received
- paddy available
- rice stock
- pending delivery
- claims pending
- amount paid
- amount outstanding

Also show:
- alerts
- recent loads
- recent milling
- recent deliveries
- recent claims

### Government Loads
List with search, filters, status, date, lorry, quantity.

### New Government Load
Sections:
- government/DO
- vehicle
- paddy
- weighment
- documents

Actions:
- Save Draft
- Save & Continue

### Load Details
Show:
- status
- government details
- vehicle
- weighment
- quality
- documents
- paddy lot
- timeline

### Paddy Stock
Show total stock and lot-level stock.

### Milling Batches
List and create batch.

New batch:
- date
- paddy lots
- quantities
- machine/line optional
- start/end
- production outputs

### Rice Production
Capture:
- Category 1 quantity
- Category 2 quantity
- bag weight
- calculated bag count
- optional by-products

### Rice QC
Capture configured QC fields and pass/fail.

### Rice Stock
Show category summary and lot-level inventory.

### Dispatch
Select destination, DO, vehicle, and rice lots.

Validate available stock and QC eligibility.

### Delivery Receipt
Record:
- dispatched quantity
- received quantity
- received bags
- shortage/excess
- receipt number/date
- receipt document

### Government Claims
List claims and statuses.

Create claim from eligible completed deliveries.

Show:
- charge lines
- rates
- gross
- deductions
- net
- PDF generation
- submission

### Payments
Show:
- claim amount
- paid
- outstanding
- payment history

### Reports
Simple filterable tables with print/PDF/export where appropriate.

### Settings
Mill profile, rice categories, bag configuration, Government charge/rate configuration, users.

## UX Rules

- Always show loading, empty, error, and success states.
- Confirm destructive/reversal actions.
- Use server-calculated totals as authoritative.
- Never hide validation errors.
- Preserve entered form data where reasonable after recoverable errors.
- Avoid excessive modals.
- Use clear status badges.
- Use consistent date/number/weight formatting.
- Use Indian number formatting where appropriate.
- Make the primary action visually obvious.
- Never make users manually calculate totals that the system can calculate safely.

## Traceability UI

Every important entity should expose related records.

Rice Lot:
→ Production
→ Milling Batch
→ Paddy Lots
→ Government Load

Government Load:
→ Paddy Lot
→ Milling Batch
→ Rice Lots
→ Dispatches
→ Claims
→ Payment

Use a timeline or related-record section rather than forcing users to search manually.
