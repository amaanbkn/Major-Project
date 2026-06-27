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
    try:
        ipos = await get_upcoming_ipos()
        return {"ipos": ipos, "count": len(ipos), "status": "success"}
    except Exception as e:
        logger.error(f"Error in IPO list: {e}")
        return {"ipos": [], "count": 0, "status": "error", "error": f"Scraping service is temporarily unavailable: {str(e)}"}


@router.get("/ipo/gmp")
async def get_gmp_data():
    """Get Grey Market Premium data for current IPOs."""
    logger.info("📊 GMP data request")
    from services.ipo_tracker import get_ipo_gmp
    try:
        gmp = await get_ipo_gmp()
        return {"gmp_data": gmp, "count": len(gmp), "status": "success"}
    except Exception as e:
        logger.error(f"Error in GMP route: {e}")
        return {"gmp_data": [], "count": 0, "status": "error", "error": f"Scraping service is temporarily unavailable: {str(e)}"}


from pydantic import BaseModel
class IPOAnalysisRequest(BaseModel):
    name: str
    band: str = "TBA"
    gmp: str = "N/A"
    estListing: str = "N/A"
    open: str = "TBA"
    close: str = "TBA"
    subscription: float = 0.0
    sector: str = "Various"

@router.post("/ipo/analyze")
async def analyze_ipo(request: IPOAnalysisRequest):
    """Analyze an IPO with Gemini AI using the IPO data as context."""
    from services.gemini import generate_response
    
    ipo_context = f"""
    IPO Details:
    - Company Name: {request.name}
    - Sector: {request.sector}
    - Price Band: {request.band}
    - Grey Market Premium (GMP): {request.gmp}
    - Estimated Listing Price: {request.estListing}
    - Open Date: {request.open}
    - Close Date: {request.close}
    - Subscription Level: {request.subscription}x
    """
    
    prompt = f"""
    Provide a concise, professional investment analysis for the IPO of {request.name}.
    Structure it cleanly using markdown:
    1. **Overview & Industry**: Brief summary of the company and prospects for the {request.sector} sector.
    2. **Valuation**: Assessment of the Price Band of {request.band}.
    3. **Market Sentiment (GMP)**: Interpretation of current GMP {request.gmp} (Est. Listing: {request.estListing}).
    4. **Subscription Interest**: What does the subscription level of {request.subscription}x suggest?
    5. **Final Verdict**: Outline key strengths, major risks, and a clear "Apply" / "Avoid" / "Wait" recommendation.
    
    Ensure all points are clear. Keep the formatting professional. Add a disclaimer.
    """
    try:
        analysis = await generate_response(prompt, context=ipo_context)
        return {"analysis": analysis, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to analyze IPO: {e}")
        return {"analysis": "The AI analysis is temporarily unavailable.", "status": "error", "error": str(e)}
