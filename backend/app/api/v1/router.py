from fastapi import APIRouter

from app.api.v1.endpoints import auth, client, health, roles

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(client.router, prefix="/clients")
api_router.include_router(health.router, prefix="/health")
api_router.include_router(roles.router, prefix="/roles")
