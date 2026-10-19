
from fastapi import APIRouter, HTTPException

from schemas.request import AdaptacionRequest
from services.adaptation_service import adaptar_contenido
from orquestacion_agentes.main import EntradaInvalida, ErrorGeneracion


router = APIRouter(
    prefix="/adapt",
    tags=["Adaptación"],
)



@router.post("/adapt")
def adapt(request: AdaptacionRequest):
    try:
        return adaptar_contenido(request)

    except EntradaInvalida as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except ErrorGeneracion as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error
