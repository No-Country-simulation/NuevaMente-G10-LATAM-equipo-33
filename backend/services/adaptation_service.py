
"""
Servicio de adaptación de contenido de NuevaMente.
Coordina la ingesta RAG, la generación, la evaluación
y el almacenamiento del contenido adaptado.
"""

from schemas.request import AdaptacionRequest
from shared.contratos import RespuestaFinal
from core.config import settings

from services.rag_service import indexar, buscar
from services.orchestration_service import generar_contenido

from evaluacion.services.evaluador import evaluar_contenido
from mocks.storage_mock import almacenar_contenido


def adaptar_contenido(request: AdaptacionRequest) -> RespuestaFinal:
    # 1. Indexar el documento.
    doc_id = indexar(
        titulo=request.documento_titulo,
        contenido=request.documento_contenido,
    )

    # 2. Recuperar el contexto relevante.
    contexto = buscar(
        doc_id=doc_id,
        query=request.documento_titulo,
        top_k=settings.top_k,
    )

    # 3. Generar contenido con la nueva orquestación.
    contenido = generar_contenido(
        documento_titulo=request.documento_titulo,
        contexto=contexto,
        perfil_destinatario=request.perfil_destinatario,
        formato_salida=request.formato_salida,
        nicho_sector=request.nicho_sector,
        nivel_detalle=request.nivel_detalle,
    )

    # 4. Evaluar el contenido generado.
    evaluacion = evaluar_contenido(
        contenido_generado=contenido,
        contexto=contexto,
        perfil_destinatario=request.perfil_destinatario,
        formato_salida=request.formato_salida,
)

    # 5. Almacenar el contenido.
    almacenamiento = almacenar_contenido(
        contenido=contenido.model_dump(),
    )

    # 6. Construir la respuesta según el contrato compartido.
    return RespuestaFinal(
        status="exito",
        metadatos={
            "perfil_aplicado": request.perfil_destinatario,
            "formato_generado": request.formato_salida,
            "tiempo_estimado_estudio_minutos": (
                contenido.tiempo_estimado_estudio_minutos
            ),
            "conceptos_clave": contenido.conceptos_clave,
        },
        contenido_adaptado=contenido,
        evaluacion_calidad=evaluacion,
        almacenamiento_oci=almacenamiento,
    )
