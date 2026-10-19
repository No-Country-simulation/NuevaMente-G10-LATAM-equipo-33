"""
Esquemas internos del evaluador (LLM como juez).

El LLM se fuerza a devolver un ResultadoJuez. Estos modelos son de uso
interno de evaluacion: hacia afuera el módulo devuelve EvaluacionCalidad
(definida en shared/contratos.py).
"""

from typing import Literal

from pydantic import BaseModel, Field

Veredicto = Literal["respaldado", "parcial", "no_respaldado"]
NivelClaridad = Literal["Alta", "Media", "Baja"]


class VeredictoItem(BaseModel):
    indice: int = Field(
        description="Posición del ítem evaluado dentro de la lista de ítems, empezando en 0."
    )
    veredicto: Veredicto = Field(
        description=(
            "'respaldado' si el contexto sustenta completamente el ítem; "
            "'parcial' si solo sustenta una parte o hay datos no presentes en el contexto; "
            "'no_respaldado' si el contexto no lo sustenta o lo contradice."
        )
    )
    justificacion: str = Field(
        description="Explicación breve, citando la fuente del contexto cuando sea posible."
    )


class ResultadoJuez(BaseModel):
    veredictos_items: list[VeredictoItem] = Field(
        description="Un veredicto por cada ítem del contenido generado."
    )
    claridad_pedagogica: NivelClaridad = Field(
        description="Qué tan claro y adecuado es el contenido para el perfil del destinatario."
    )
    observaciones: str = Field(
        description="Resumen breve: qué está bien, qué ítems fallan y por qué."
    )