from shared.contratos import (
    ChunkResultado,
    ContenidoGenerado,
)


def generar_contenido_adaptado(
    documento_titulo: str,
    contexto: list[ChunkResultado],
    perfil_destinatario: str,
    formato_salida: str,
    nicho_sector: str,
    nivel_detalle: str,
) -> ContenidoGenerado:

    return ContenidoGenerado(
        titulo=f"{documento_titulo} - Contenido adaptado",
        introduccion_contextualizada=(
            f"Contenido adaptado para el perfil "
            f"{perfil_destinatario}."
        ),
        items=[
            {
                "tipo": formato_salida,
                "contenido": "Contenido educativo generado por MOCK."
            }
        ],
        conceptos_clave=[
            "concepto-1",
            "concepto-2",
        ],
        tiempo_estimado_estudio_minutos=5,
    )