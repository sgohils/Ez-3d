from fastapi import APIRouter

from api.v1.endpoints.export_endpoint import router as export_router
from api.v1.endpoints.generate import router as generate_router
from api.v1.endpoints.recompile import router as recompile_router

router = APIRouter(prefix="/api/v1", tags=["v1"])

router.include_router(generate_router)
router.include_router(recompile_router)
router.include_router(export_router)


@router.get("/health")
async def v1_health() -> dict:
    return {"status": "ok", "version": "0.1.0"}