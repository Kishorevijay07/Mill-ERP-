"""RBAC permission catalogue and Phase-1 default role grants.

Permission *codes* are defined here in code (the authoritative catalogue). Grants
are stored per-role in the ``role_permissions`` table so an administrator can
later adjust them, and so future roles (Gate Operator, Store Manager, …) can be
introduced without schema changes.

A permission code is a dotted ``domain.resource.action`` string. Keep this list
aligned with docs/SECURITY.md as modules are implemented.
"""

from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    # Government master data & receiving
    GOVERNMENT_AGENCY_VIEW = "government.agency.view"
    GOVERNMENT_AGENCY_MANAGE = "government.agency.manage"
    GOVERNMENT_ALLOCATION_VIEW = "government.allocation.view"
    GOVERNMENT_ALLOCATION_MANAGE = "government.allocation.manage"
    GOVERNMENT_DELIVERY_ORDER_VIEW = "government.delivery_order.view"
    GOVERNMENT_DELIVERY_ORDER_MANAGE = "government.delivery_order.manage"
    GOVERNMENT_LOAD_CREATE = "government.load.create"
    GOVERNMENT_LOAD_VIEW = "government.load.view"
    GOVERNMENT_LOAD_ACCEPT = "government.load.accept"

    # Receiving operations
    RECEIVING_WEIGHMENT_RECORD = "receiving.weighment.record"
    RECEIVING_PADDY_QC_RECORD = "receiving.paddy_quality.record"

    # Paddy stock
    PADDY_STOCK_VIEW = "paddy.stock.view"
    PADDY_STOCK_ADJUST = "paddy.stock.adjust"

    # Milling
    MILLING_BATCH_CREATE = "milling.batch.create"
    MILLING_BATCH_VIEW = "milling.batch.view"

    # Rice QC & stock
    RICE_QC_APPROVE = "rice.qc.approve"
    RICE_STOCK_VIEW = "rice.stock.view"

    # Dispatch & delivery
    DISPATCH_CREATE = "dispatch.create"
    DISPATCH_VIEW = "dispatch.view"
    DISPATCH_CONFIRM = "dispatch.confirm"

    # Billing
    BILLING_CREATE = "billing.create"
    BILLING_VIEW = "billing.view"
    BILLING_SUBMIT = "billing.submit"
    BILLING_APPROVE = "billing.approve"
    PAYMENT_RECORD = "payment.record"

    # Invoicing (commercial GST tax invoices + buyer/product masters)
    INVOICE_VIEW = "invoice.view"
    INVOICE_CREATE = "invoice.create"
    INVOICE_ISSUE = "invoice.issue"
    INVOICE_MASTERS_MANAGE = "invoice.masters.manage"

    # Cross-cutting
    REPORTS_VIEW = "reports.view"
    SETTINGS_VIEW = "settings.view"
    SETTINGS_MANAGE = "settings.manage"
    USERS_MANAGE = "users.manage"


ALL_PERMISSIONS: frozenset[str] = frozenset(p.value for p in Permission)


class RoleCode(StrEnum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    STAFF = "STAFF"


# Read/view + operational subset shared by day-to-day staff.
_STAFF_PERMISSIONS: frozenset[str] = frozenset(
    {
        Permission.GOVERNMENT_AGENCY_VIEW,
        Permission.GOVERNMENT_ALLOCATION_VIEW,
        Permission.GOVERNMENT_DELIVERY_ORDER_VIEW,
        Permission.GOVERNMENT_LOAD_CREATE,
        Permission.GOVERNMENT_LOAD_VIEW,
        Permission.RECEIVING_WEIGHMENT_RECORD,
        Permission.RECEIVING_PADDY_QC_RECORD,
        Permission.PADDY_STOCK_VIEW,
        Permission.MILLING_BATCH_CREATE,
        Permission.MILLING_BATCH_VIEW,
        Permission.RICE_STOCK_VIEW,
        Permission.DISPATCH_CREATE,
        Permission.DISPATCH_VIEW,
        Permission.REPORTS_VIEW,
        Permission.INVOICE_VIEW,
        Permission.INVOICE_CREATE,
    }
)

# Owner: everything staff can do plus approvals/acceptance and billing, but not
# user/settings administration (which is ADMIN-only).
_OWNER_PERMISSIONS: frozenset[str] = _STAFF_PERMISSIONS | frozenset(
    {
        Permission.GOVERNMENT_AGENCY_MANAGE,
        Permission.GOVERNMENT_ALLOCATION_MANAGE,
        Permission.GOVERNMENT_DELIVERY_ORDER_MANAGE,
        Permission.GOVERNMENT_LOAD_ACCEPT,
        Permission.PADDY_STOCK_ADJUST,
        Permission.RICE_QC_APPROVE,
        Permission.DISPATCH_CONFIRM,
        Permission.BILLING_CREATE,
        Permission.BILLING_VIEW,
        Permission.BILLING_SUBMIT,
        Permission.BILLING_APPROVE,
        Permission.PAYMENT_RECORD,
        Permission.INVOICE_ISSUE,
        Permission.INVOICE_MASTERS_MANAGE,
        Permission.SETTINGS_VIEW,
    }
)

# Default grants seeded for the system roles. ADMIN is granted the full catalogue.
DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    RoleCode.ADMIN: ALL_PERMISSIONS,
    RoleCode.OWNER: _OWNER_PERMISSIONS,
    RoleCode.STAFF: _STAFF_PERMISSIONS,
}

DEFAULT_ROLE_DESCRIPTIONS: dict[str, str] = {
    RoleCode.ADMIN: "Full administrative access, including users and settings.",
    RoleCode.OWNER: "Mill owner: operations, approvals, billing and payments.",
    RoleCode.STAFF: "Day-to-day operational staff.",
}
