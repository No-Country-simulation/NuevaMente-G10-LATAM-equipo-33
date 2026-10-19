"""
Adaptador del backend hacia orquestacion_agentes.
"""

from shared.contratos import ChunkResultado, ContenidoGenerado

from orquestacion_agentes.main import generar_contenido_adaptado


def generar_contenido(
    documento_titulo: str,
    contexto: list[ChunkResultado],
    perfil_destinatario: str,
    formato_salida: str,
    nicho_sector: str,
    nivel_detalle: str,
) -> ContenidoGenerado:
    """
    Delega la generación de contenido al módulo de orquestación.
    """
    return generar_contenido_adaptado(
        documento_titulo=documento_titulo,
        contexto=contexto,
        perfil_destinatario=perfil_destinatario,
        formato_salida=formato_salida,
        nicho_sector=nicho_sector,
        nivel_detalle=nivel_detalle,
    )