from schemas.request import AdaptacionRequest
from shared.contratos import RespuestaFinal


from mocks.rag_mock import (
    indexar_documento,
    buscar_contexto,
)

from mocks.orchestration_mock import (
    generar_contenido_adaptado,
)

from mocks.evaluation_mock import (
    evaluar_contenido,
)

from mocks.storage_mock import (
    almacenar_contenido,
)


def adaptar_contenido(
    request: AdaptacionRequest,
) -> RespuestaFinal:

    # 1. Indexar documento
    doc_id = indexar_documento(
        request.documento_titulo,
        request.documento_contenido,
    )

    # 2. Buscar contexto
    contexto = buscar_contexto(
        doc_id=doc_id,
        query=request.documento_titulo,
    )

    # 3. Generar contenido adaptado
    contenido = generar_contenido_adaptado(
        documento_titulo=request.documento_titulo,
        contexto=contexto,
        perfil_destinatario=request.perfil_destinatario,
        formato_salida=request.formato_salida,
        nicho_sector=request.nicho_sector,
        nivel_detalle=request.nivel_detalle,
    )

    # 4. Evaluar
    evaluacion = evaluar_contenido(
        contenido=contenido,
        contexto=contexto,
    )

    # 5. Almacenar
    almacenamiento = almacenar_contenido(
        contenido=contenido.model_dump(),
    )

    # 6. Construir respuesta final
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