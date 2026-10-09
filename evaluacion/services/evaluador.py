"""
Servicio de evaluación de calidad (LLM como juez).

Compara el contenido generado por orquestacion-agentes contra el contexto
original recuperado por ingesta-rag. El LLM emite un veredicto por ítem y el
código calcula el score, para que el resultado sea reproducible y explicable.
"""

from schemas.juez import VeredictoItem

# Peso de cada veredicto en el score de anclaje.
PESOS_VEREDICTO = {"respaldado": 1.0, "parcial": 0.5, "no_respaldado": 0.0}


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