from fastapi import APIRouter
from . import dashboard, pokemon, habitats, playground, mongo_viewer, mongo_playground, keepers, species, foods, schedules, reports

router = APIRouter()

router.include_router(dashboard.router, tags=["admin-dashboard"])
router.include_router(foods.router, prefix="/foods", tags=["admin-foods"])
router.include_router(schedules.router, prefix="/schedules", tags=["admin-schedules"])
router.include_router(species.router, prefix="/species", tags=["admin-species"])
router.include_router(pokemon.router, prefix="/pokemon", tags=["admin-pokemon"])
router.include_router(habitats.router, prefix="/habitats", tags=["admin-habitats"])
router.include_router(keepers.router, prefix="/keepers", tags=["admin-keepers"])
router.include_router(playground.router, tags=["admin-playground"])
router.include_router(mongo_viewer.router, tags=["admin-mongo-viewer"])
router.include_router(mongo_playground.router, tags=["admin-mongo-playground"])
router.include_router(reports.router, tags=["admin-reports"])
