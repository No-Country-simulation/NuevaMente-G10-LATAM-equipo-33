from fastapi import APIRouter

from schemas.request import AdaptacionRequest
from services.adaptation_service import adaptar_contenido

router = APIRouter(
    prefix="/adapt",
    tags=["Adaptación"],
)


@router.post("")
def adapt(request: AdaptacionRequest):
    return adaptar_contenido(request)