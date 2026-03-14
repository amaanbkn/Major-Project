"""
FinSight AI — IPO Router
GET /api/ipo — IPO calendar + GMP data.
"""

from fastapi import APIRouter
from loguru import logger

router = APIRouter()


@router.get("/ipo")
async def get_ipo_list():
    """Get list of upcoming/current IPOs with GMP data."""
    logger.info("📋 IPO data request")
    from services.ipo_tracker import get_upcoming_ipos
    ipos = await get_upcoming_ipos()
    return {"ipos": ipos, "count": len(ipos)}


@router.get("/ipo/gmp")
async def get_gmp_data():
    """Get Grey Market Premium data for current IPOs."""
    logger.info("📊 GMP data request")
    from services.ipo_tracker import get_ipo_gmp
    gmp = await get_ipo_gmp()
    return {"gmp_data": gmp, "count": len(gmp)}
