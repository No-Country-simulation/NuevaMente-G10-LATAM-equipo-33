"""
Modelos Pydantic para intercambio y validación interna de datos.
Alineados estrictamente con contratos.txt.
"""

from pydantic import BaseModel, Field


class ChunkResultado(BaseModel):
    texto: str = Field(..., description="Texto del fragmento recuperado")
    score: float = Field(..., description="Similitud semántica (0 a 1)")
    fuente: str = Field(..., description="Ubicación o fragmento de donde proviene")


class IndexRequest(BaseModel):
    documento_titulo: str
    documento_contenido: str