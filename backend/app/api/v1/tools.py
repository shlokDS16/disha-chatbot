from fastapi import APIRouter

from app.models.schemas import PunnettRequest, PunnettResponse
from app.services.punnett import calculate_punnett

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/punnett", response_model=PunnettResponse)
def punnett(body: PunnettRequest) -> PunnettResponse:
    return calculate_punnett(body.parent1_hb, body.parent2_hb, body.language)
