"""
FinSight AI — SIP Router
POST /api/sip — SIP recommendation based on risk profiling.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

router = APIRouter()


class SIPRequest(BaseModel):
    """SIP recommendation request."""
    risk_level: str = Field(..., description="low, medium, or high")
    monthly_amount: float = Field(..., gt=0, description="Monthly SIP amount in ₹")
    goal_years: int = Field(..., gt=0, le=50, description="Investment horizon in years")


@router.post("/sip")
async def get_sip_recommendation(request: SIPRequest):
    """
    Get SIP recommendation based on risk appetite.
    - Risk level: low, medium, high
    - Monthly amount: ₹ value
    - Goal years: investment horizon
    Returns fund allocation + projected returns.
    """
    if request.risk_level.lower() not in ("low", "medium", "high"):
        raise HTTPException(
            status_code=400,
            detail="risk_level must be one of: low, medium, high",
        )

    logger.info(
        f"📊 SIP request: {request.risk_level}, ₹{request.monthly_amount}/mo, {request.goal_years}yr"
    )

    from agents.recommendation_engine import get_sip_recommendation

    result = get_sip_recommendation(
        risk_level=request.risk_level,
        monthly_amount=request.monthly_amount,
        goal_years=request.goal_years,
    )

    return result
