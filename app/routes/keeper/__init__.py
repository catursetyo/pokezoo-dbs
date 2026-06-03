from fastapi import APIRouter
from . import dashboard, mongo_routes

router = APIRouter()

router.include_router(dashboard.router, tags=["keeper-dashboard"])
router.include_router(mongo_routes.router, tags=["keeper-mongo"])
