from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    clients,
    employees,
    employee_compensation_payments,
    events,
    event_staff_assignments,
    expenses,
    expense_payments,
    financial_audit_logs,
    health,
    quotes,
    payments,
    platform_memberships,
    platform_tenants,
    platform_users,
    products,
    product_categories,
    roles,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(clients.router, prefix="/clients")
api_router.include_router(employees.router, prefix="/employees")
api_router.include_router(employee_compensation_payments.router, prefix="/employee-compensation-payments")
api_router.include_router(events.router, prefix="/events")
api_router.include_router(event_staff_assignments.router, prefix="/event-staff-assignments")
api_router.include_router(expenses.router, prefix="/expenses")
api_router.include_router(expense_payments.router, prefix="/expense-payments")
api_router.include_router(financial_audit_logs.router, prefix="/financial-audit-logs")
api_router.include_router(health.router, prefix="/health")
api_router.include_router(quotes.router, prefix="/quotes")
api_router.include_router(payments.router, prefix="/payments")
api_router.include_router(platform_memberships.router, prefix="/platform-memberships")
api_router.include_router(platform_tenants.router, prefix="/platform-tenants")
api_router.include_router(platform_users.router, prefix="/platform-users")
api_router.include_router(products.router, prefix="/products")
api_router.include_router(product_categories.router, prefix="/product-categories")
api_router.include_router(roles.router, prefix="/roles")
