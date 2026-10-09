"""
Servicio de evaluación de calidad (LLM como juez).

Compara el contenido generado por orquestacion-agentes contra el contexto
original recuperado por ingesta-rag. El LLM emite un veredicto por ítem y el
código calcula el score, para que el resultado sea reproducible y explicable.
"""

import json
import os
import sys
from functools import lru_cache
from pathlib import Path

# Agrega la raíz del repo al path, así Python encuentra shared/
# sin importar desde qué carpeta se ejecute.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.juez import PROMPT_JUEZ
from schemas.juez import ResultadoJuez, VeredictoItem
from shared.contratos import ChunkResultado, ContenidoGenerado, EvaluacionCalidad

load_dotenv()

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Peso de cada veredicto en el score de anclaje.
PESOS_VEREDICTO = {"respaldado": 1.0, "parcial": 0.5, "no_respaldado": 0.0}


@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    """Crea el LLM la primera vez que se usa (así importar el módulo no exige API key)."""
    return ChatGoogleGenerativeAI(
        model=MODELO,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=3,
    )


def calcular_anclaje(veredictos: list[VeredictoItem], total_items: int) -> float:
    """Score de 0 a 1: promedio del peso de cada ítem.

    Los ítems sin veredicto cuentan como no respaldados, y los índices fuera
    de rango o repetidos se ignoran, para que un LLM descuidado no infle el score.
    """
    if total_items <= 0:
        return 0.0

    por_indice: dict[int, VeredictoItem] = {}
    for v in veredictos:
        if 0 <= v.indice < total_items and v.indice not in por_indice:
            por_indice[v.indice] = v

    total = sum(PESOS_VEREDICTO[v.veredicto] for v in por_indice.values())
    return round(total / total_items, 2)


def _indices_a_revisar(veredictos: list[VeredictoItem], total_items: int) -> list[int]:
    """Índices de ítems que no están completamente respaldados (incluye los omitidos)."""
    respaldados = {v.indice for v in veredictos if v.veredicto == "respaldado"}
    return [i for i in range(total_items) if i not in respaldados]


def _formatear_contexto(contexto: list[ChunkResultado]) -> str:
    return "\n\n".join(f"[Fuente: {c.fuente}]\n{c.texto}" for c in contexto)


def _formatear_items(items: list[dict]) -> str:
    return "\n".join(
        f"[{i}] {json.dumps(item, ensure_ascii=False)}" for i, item in enumerate(items)
    )


def evaluar_contenido(
    contenido_generado: ContenidoGenerado,
    contexto: list[ChunkResultado],
    perfil_destinatario: str,
    formato_salida: str,
) -> EvaluacionCalidad:
    """Evalúa la fidelidad a la fuente y la claridad pedagógica del contenido."""
    total_items = len(contenido_generado.items)

    if total_items == 0:
        return EvaluacionCalidad(
            anclaje_fuente_score=0.0,
            claridad_pedagogica="Baja",
            observaciones="El contenido generado no tiene ítems para evaluar.",
        )

    prompt = PROMPT_JUEZ.format(
        contexto_texto=_formatear_contexto(contexto),
        titulo=contenido_generado.titulo,
        perfil_destinatario=perfil_destinatario,
        formato_salida=formato_salida,
        items_texto=_formatear_items(contenido_generado.items),
    )

    juez = _get_llm().with_structured_output(ResultadoJuez)
    resultado: ResultadoJuez = juez.invoke(prompt)

    score = calcular_anclaje(resultado.veredictos_items, total_items)
    observaciones = resultado.observaciones
    a_revisar = _indices_a_revisar(resultado.veredictos_items, total_items)
    if a_revisar:
        observaciones += f" Ítems a revisar (índice desde 0): {a_revisar}."

    return EvaluacionCalidad(
        anclaje_fuente_score=score,
        claridad_pedagogica=resultado.claridad_pedagogica,
        observaciones=observaciones,
    )