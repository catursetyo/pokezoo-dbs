from fastapi import APIRouter
from . import visitor_routes

router = APIRouter()
router.include_router(visitor_routes.router)
