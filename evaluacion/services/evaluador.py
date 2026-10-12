"""
Servicio de evaluación de calidad (LLM como juez).

Compara el contenido generado por orquestacion-agentes contra el contexto
original recuperado por ingesta-rag. El LLM emite un veredicto por ítem y el
código calcula el score, para que el resultado sea reproducible y explicable.

evaluar_contenido nunca lanza error por fallas de Gemini: si no puede evaluar,
devuelve una EvaluacionCalidad con score 0.0 y claridad "No evaluada".
"""

import json
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path

# Agrega la raíz del repo al path, así Python encuentra shared/
# sin importar desde qué carpeta se ejecute.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from evaluacion.prompts.juez import PROMPT_JUEZ
from evaluacion.schemas.juez import ResultadoJuez, VeredictoItem
from shared.contratos import ChunkResultado, ContenidoGenerado, EvaluacionCalidad

load_dotenv()
logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "gemini-3.6-flash"
MODELO_RESPALDO_POR_DEFECTO = "gemini-3.8-flash"

# Peso de cada veredicto en el score de anclaje.
PESOS_VEREDICTO = {"respaldado": 1.0, "parcial": 0.5, "no_respaldado": 0.0}

# Índice de la última API key que funcionó (así no se vuelve a golpear una agotada).
_clave_actual = 0


class ErrorEvaluacion(Exception):
    """No hubo forma de usar Gemini (sin key, sin cupo o modelos saturados)."""


def _obtener_api_keys() -> list[str]:
    """Todas las keys configuradas en el .env, en orden y sin repetir."""
    claves = []
    for nombre in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        valor = os.getenv(nombre, "").strip()
        if valor:
            claves.append(valor)
    claves += [c.strip() for c in os.getenv("GEMINI_API_KEYS", "").split(",") if c.strip()]
    return list(dict.fromkeys(claves))


def _obtener_modelos() -> list[str]:
    """Modelo principal y modelo de respaldo, en orden y sin repetir."""
    principal = os.getenv("GEMINI_MODEL", "").strip() or MODELO_POR_DEFECTO
    respaldo = os.getenv("GEMINI_MODEL_RESPALDO", MODELO_RESPALDO_POR_DEFECTO).strip()
    return list(dict.fromkeys(m for m in (principal, respaldo) if m))


@lru_cache(maxsize=None)
def _get_llm(modelo: str, api_key: str) -> ChatGoogleGenerativeAI:
    """Crea el LLM de un modelo y una key la primera vez que se usa (importar no exige API key)."""
    return ChatGoogleGenerativeAI(
        model=modelo,
        google_api_key=api_key,
        max_retries=1,
    )


def _es_error_de_sobrecarga(error: Exception) -> bool:
    """503: el modelo está saturado para todos, cambiar de key no ayuda."""
    texto = f"{type(error).__name__} {error}".upper()
    return "UNAVAILABLE" in texto or "503" in texto or "OVERLOADED" in texto


def _es_error_de_cuota(error: Exception) -> bool:
    """429: esta key agotó su cupo, otra key puede tener."""
    texto = f"{type(error).__name__} {error}".upper()
    return "RESOURCE_EXHAUSTED" in texto or "RATELIMIT" in texto or "429" in texto


def _invocar_con_rotacion(prompt: str) -> ResultadoJuez:
    """Llama al juez rotando keys ante errores de cupo y modelos ante saturación."""
    global _clave_actual

    claves = _obtener_api_keys()
    if not claves:
        raise ErrorEvaluacion("falta configurar la API key de Gemini")

    ultimo_error = None
    for modelo in _obtener_modelos():
        for desplazamiento in range(len(claves)):
            indice = (_clave_actual + desplazamiento) % len(claves)
            try:
                juez = _get_llm(modelo, claves[indice]).with_structured_output(ResultadoJuez)
                resultado = juez.invoke(prompt)
            except Exception as error:
                if _es_error_de_sobrecarga(error):
                    logger.warning("El modelo %s está saturado, se prueba el siguiente: %s", modelo, error)
                    ultimo_error = error
                    break  # con el modelo saturado otra key no ayuda: siguiente modelo
                if _es_error_de_cuota(error):
                    logger.warning("La API key %d no tiene cupo, se prueba la siguiente: %s", indice + 1, error)
                    ultimo_error = error
                    continue
                raise
            _clave_actual = indice
            return resultado

    raise ErrorEvaluacion("cupo agotado o modelos saturados en todas las API keys") from ultimo_error


def _evaluacion_no_disponible(motivo: str) -> EvaluacionCalidad:
    return EvaluacionCalidad(
        anclaje_fuente_score=0.0,
        claridad_pedagogica="No evaluada",
        observaciones=(
            f"No se pudo completar la evaluación automática ({motivo}). "
            "Revisar el contenido manualmente."
        ),
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

    try:
        resultado = _invocar_con_rotacion(prompt)
    except ErrorEvaluacion as error:
        logger.warning("No se pudo evaluar el contenido con Gemini: %s", error)
        return _evaluacion_no_disponible(str(error))
    except Exception as error:
        logger.warning("No se pudo evaluar el contenido con Gemini: %s", error)
        return _evaluacion_no_disponible(type(error).__name__)

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