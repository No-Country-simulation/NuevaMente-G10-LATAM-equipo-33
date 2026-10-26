
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.schemas.request import AdaptacionRequest
from backend.services.adaptation_service import adaptar_contenido
from orquestacion_agentes.main import EntradaInvalida, ErrorGeneracion
from backend.core.config import settings
from backend.services.extraction_service import extraer_texto
from backend.core.exceptions import StorageError


router = APIRouter(
    prefix="/adapt",
    tags=["Adaptación"],
)



@router.post("")
def adapt(
    archivo: UploadFile = File(...),
    perfil_destinatario: str = Form(..., min_length=1),
    formato_salida: str = Form(..., min_length=1),
    nicho_sector: str = Form(..., min_length=1),
    nivel_detalle: str = Form(..., min_length=1),
):
    try:
        limite = settings.max_upload_mb * 1024 * 1024
        datos = archivo.file.read(limite + 1)
        if len(datos) > limite:
            raise HTTPException(413, "El archivo supera el tamaño permitido.")
        nombre = (archivo.filename or "documento").replace("\\", "/").rsplit("/", 1)[-1]
        request = AdaptacionRequest(
            documento_titulo=nombre or "documento",
            documento_contenido=extraer_texto(nombre, datos),
            perfil_destinatario=perfil_destinatario,
            formato_salida=formato_salida,
            nicho_sector=nicho_sector,
            nivel_detalle=nivel_detalle,
        )
        return adaptar_contenido(request, documento_bytes=datos)

    except StorageError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from None

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
    finally:
        archivo.file.close()
