from fastapi import APIRouter

from app.api.v1 import chat, contract, health, legal_search

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(legal_search.router)
api_router.include_router(contract.router)
