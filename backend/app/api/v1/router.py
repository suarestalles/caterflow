from fastapi import APIRouter

from app.api.v1.endpoints import auth, clients, employees, events, event_staff_assignments, health, quotes, products, product_categories, roles

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(clients.router, prefix="/clients")
api_router.include_router(employees.router, prefix="/employees")
api_router.include_router(events.router, prefix="/events")
api_router.include_router(event_staff_assignments.router, prefix="/event-staff-assignments")
api_router.include_router(health.router, prefix="/health")
api_router.include_router(quotes.router, prefix="/quotes")
api_router.include_router(products.router, prefix="/products")
api_router.include_router(product_categories.router, prefix="/product-categories")
api_router.include_router(roles.router, prefix="/roles")
