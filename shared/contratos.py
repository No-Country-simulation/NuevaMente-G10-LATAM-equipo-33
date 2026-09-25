"""

Este archivo define las funciones que cada modulo debe exponer
para poder ser consumido por otro modulo dependiente

Este archivo debe ser importado por ingesta-rag,
orquestacion-agentes y backend. Es la única fuente de verdad de las
estructuras de datos que se pasan entre módulos

No modificar sin avisar al equipo, ya que un cambio acá rompe a quien consuma
la función correspondiente en otro módulo.
"""

from pydantic import BaseModel
from typing import Any


# ── Contrato 1: ingesta-rag → orquestacion-agentes ──────────────

class ChunkResultado(BaseModel):
    texto: str
    score: float           # similitud (0 a 1)
    fuente: str             # de qué parte del documento viene (ej: sección, página)


def indexar_documento(documento_titulo: str, documento_contenido: str) -> str:
    """Chunkea, genera embeddings, indexa en el vector store.
    Devuelve un doc_id para referenciarlo después.
    Implementación real: módulo ingesta-rag."""
    raise NotImplementedError


def buscar_contexto(doc_id: str, query: str, top_k: int = 5) -> list[ChunkResultado]:
    """Busca los chunks más relevantes dentro de ese documento ya indexado.
    Implementación real: módulo ingesta-rag."""
    raise NotImplementedError


# ── Contrato 2: orquestacion-agentes → backend ───────────────────

class ContenidoGenerado(BaseModel):
    titulo: str
    introduccion_contextualizada: str
    items: list[dict[str, Any]]        # estructura varía según formato_salida
    conceptos_clave: list[str]
    tiempo_estimado_estudio_minutos: int


def generar_contenido_adaptado(
    documento_titulo: str,
    contexto: list[ChunkResultado],
    perfil_destinatario: str,
    formato_salida: str,
    nicho_sector: str,
    nivel_detalle: str,
) -> ContenidoGenerado:
    """Le pasa el contexto recuperado al LLM, adapta según los parámetros.
    Implementación real: módulo orquestacion-agentes."""
    raise NotImplementedError


# ── Contrato 3: backend arma la respuesta final ──────────────────
# (usa evaluacion + oci-storage además de orquestacion-agentes)

class EvaluacionCalidad(BaseModel):
    anclaje_fuente_score: float
    claridad_pedagogica: str
    observaciones: str


class AlmacenamientoOCI(BaseModel):
    bucket: str
    objeto_id: str
    status_upload: str


class RespuestaFinal(BaseModel):
    status: str
    metadatos: dict[str, Any]
    contenido_adaptado: ContenidoGenerado
    evaluacion_calidad: EvaluacionCalidad
    almacenamiento_oci: AlmacenamientoOCI