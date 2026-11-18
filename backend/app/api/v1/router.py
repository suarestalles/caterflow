from fastapi import APIRouter

from app.api.v1.endpoints import auth, clients, events, health, quotes, roles

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(clients.router, prefix="/clients")
api_router.include_router(events.router, prefix="/events")
api_router.include_router(health.router, prefix="/health")
api_router.include_router(quotes.router, prefix="/quotes")
api_router.include_router(roles.router, prefix="/roles")
