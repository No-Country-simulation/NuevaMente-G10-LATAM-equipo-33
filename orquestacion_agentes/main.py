"""
Módulo orquestacion-agentes — NuevaMente

Recibe el contexto recuperado por ingesta-rag y, vía Gemini, genera el
contenido adaptado según perfil, formato y nicho solicitados.

Implementa el contrato definido en shared/contratos.py:
  entrada:  list[ChunkResultado]  (viene de ingesta-rag)
  salida:   ContenidoGenerado     (va hacia backend)

Errores que puede lanzar generar_contenido_adaptado (todos definidos acá):
  EntradaInvalida     un parámetro está vacío o mal formado (es un ValueError)
  FormatoNoSoportado  el formato pedido no existe (es una EntradaInvalida)
  ErrorGeneracion     falló la generación con Gemini (cupo agotado o modelos saturados)
"""

import logging
import os
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

# Agrega la raíz del repo al path, así Python encuentra shared/
# sin importar desde qué carpeta se ejecute este archivo.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from shared.gemini_policy import StructuredResultError, invoke_models

from shared.contratos import (
    ChunkResultado,
    ContenidoGenerado,
    ContenidoFlashcards,
    ContenidoQuiz,
)

load_dotenv()
logger = logging.getLogger(__name__)

MODELO_POR_DEFECTO = "gemini-3.6-flash"
MODELO_RESPALDO_POR_DEFECTO = "gemini-3.8-flash"

NICHO_POR_DEFECTO = "General"
NIVEL_DETALLE_POR_DEFECTO = "Didactico"
MAX_GENERATED_ITEMS = 10

# Índice de la última API key que funcionó (así no se vuelve a golpear una agotada).
_clave_actual = 0


class ErrorOrquestacion(Exception):
    """Base de todos los errores de este módulo."""


class EntradaInvalida(ErrorOrquestacion, ValueError):
    """Un parámetro de entrada está vacío o mal formado."""


class FormatoNoSoportado(EntradaInvalida):
    """El formato de salida pedido no está disponible."""


class ErrorGeneracion(ErrorOrquestacion):
    """Falló la generación del contenido con el modelo."""


# Mapeo formato_salida -> modelo Pydantic tipado que fuerza la estructura
# correcta de "items" para ese formato específico.
MODELOS_POR_FORMATO = {
    "Flashcards": ContenidoFlashcards,
    "Quiz": ContenidoQuiz,
}


def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y sin espacios ni símbolos: 'Flash-Cards ' -> 'flashcards'."""
    sin_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sin_acentos.lower())


# Formatos indexados por nombre normalizado, para aceptar cualquier escritura.
_FORMATOS = {
    _normalizar(nombre): (nombre, modelo) for nombre, modelo in MODELOS_POR_FORMATO.items()
}


PROMPT_TEMPLATE = """Sos un experto en educación técnica. Tu tarea es adaptar
contenido técnico para un destinatario específico.

DOCUMENTO ORIGINAL: {documento_titulo}

CONTEXTO RELEVANTE:
{contexto_texto}

PARÁMETROS DE ADAPTACIÓN:
- Perfil del destinatario: {perfil_destinatario}
- Formato de salida: {formato_salida}
- Sector/nicho: {nicho_sector}
- Nivel de detalle: {nivel_detalle}

Generá el contenido adaptado respetando fielmente la información del
contexto (no inventes datos que no estén ahí). Ajustá el lenguaje y la
profundidad al perfil indicado, y estructuralo según el formato pedido.
Generá como máximo {max_items} elementos: flashcards o preguntas de quiz.
Podés generar menos si el contexto no justifica más; no agregues contenido de relleno.
"""


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
        timeout=60,
    )


def _invocar_con_rotacion(modelo_formato, prompt: str):
    """Llama a Gemini rotando keys ante errores de cupo y modelos ante saturación."""
    global _clave_actual

    claves = _obtener_api_keys()
    if not claves:
        raise ErrorGeneracion(
            "Falta configurar la API key de Gemini "
            "(GEMINI_API_KEYS, GEMINI_API_KEY o GOOGLE_API_KEY)."
        )

    def validate(resultado):
        if not isinstance(resultado, modelo_formato) or not resultado.items:
            raise StructuredResultError("Contenido estructurado no válido.")

    resultado, indice = invoke_models(
        models=_obtener_modelos(), keys=claves, start_index=_clave_actual,
        prepare=lambda modelo, clave: _get_llm(modelo, clave).with_structured_output(modelo_formato),
        validate=validate, prompt=prompt, error_type=ErrorGeneracion,
    )
    _clave_actual = indice
    return resultado


def _texto_requerido(campo: str, valor) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise EntradaInvalida(f"El campo '{campo}' es obligatorio y no puede estar vacío.")
    return valor.strip()


def _texto_opcional(valor, por_defecto: str) -> str:
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return por_defecto


def _resolver_formato(formato_salida) -> tuple[str, type]:
    """Devuelve (nombre oficial del formato, modelo Pydantic) sin importar cómo se escribió."""
    texto = _texto_requerido("formato_salida", formato_salida)
    encontrado = _FORMATOS.get(_normalizar(texto))
    if encontrado is None:
        raise FormatoNoSoportado(
            f"Formato '{texto}' no soportado. "
            f"Formatos disponibles: {list(MODELOS_POR_FORMATO.keys())}"
        )
    return encontrado


def _validar_contexto(contexto) -> None:
    """Valida por estructura (no por clase): ingesta-rag tiene su propia copia de ChunkResultado."""
    if not isinstance(contexto, list):
        raise EntradaInvalida("El contexto debe ser una lista de ChunkResultado.")
    for chunk in contexto:
        if not all(hasattr(chunk, campo) for campo in ("texto", "score", "fuente")):
            raise EntradaInvalida(
                "Cada elemento del contexto debe tener texto, score y fuente (ChunkResultado)."
            )
    if not any(isinstance(c.texto, str) and c.texto.strip() for c in contexto):
        raise EntradaInvalida(
            "El contexto está vacío: no hay información de la fuente para generar el contenido."
        )


def generar_contenido_adaptado(
    documento_titulo: str,
    contexto: list[ChunkResultado],
    perfil_destinatario: str,
    formato_salida: str,
    nicho_sector: str,
    nivel_detalle: str,
) -> ContenidoGenerado:
    documento_titulo = _texto_requerido("documento_titulo", documento_titulo)
    perfil_destinatario = _texto_requerido("perfil_destinatario", perfil_destinatario)
    formato_oficial, modelo_formato = _resolver_formato(formato_salida)
    nicho_sector = _texto_opcional(nicho_sector, NICHO_POR_DEFECTO)
    nivel_detalle = _texto_opcional(nivel_detalle, NIVEL_DETALLE_POR_DEFECTO)
    _validar_contexto(contexto)

    contexto_texto = "\n\n".join(
        f"[Fuente: {c.fuente} | relevancia: {c.score:.2f}]\n{c.texto}"
        for c in contexto
    )

    prompt = PROMPT_TEMPLATE.format(
        documento_titulo=documento_titulo,
        contexto_texto=contexto_texto,
        perfil_destinatario=perfil_destinatario,
        formato_salida=formato_oficial,
        nicho_sector=nicho_sector,
        nivel_detalle=nivel_detalle,
        max_items=MAX_GENERATED_ITEMS,
    )

    try:
        resultado_tipado = _invocar_con_rotacion(modelo_formato, prompt)
    except ErrorGeneracion:
        raise
    except Exception as error:
        logger.warning("Falló la generación con Gemini; detalles externos omitidos.")
        raise ErrorGeneracion(
            "No se pudo generar el contenido con Gemini. "
            "Intentá de nuevo en unos minutos."
        ) from None

    if resultado_tipado is None or not resultado_tipado.items:
        raise ErrorGeneracion("Gemini devolvió un contenido vacío. Intentá de nuevo.")

    # Normaliza al contrato genérico: items pasa de objetos tipados
    # (ItemFlashcard/ItemQuiz) a dict[str, Any] plano.
    return ContenidoGenerado(
        titulo=resultado_tipado.titulo,
        introduccion_contextualizada=resultado_tipado.introduccion_contextualizada,
        items=[item.model_dump() for item in resultado_tipado.items[:MAX_GENERATED_ITEMS]],
        conceptos_clave=resultado_tipado.conceptos_clave,
        tiempo_estimado_estudio_minutos=resultado_tipado.tiempo_estimado_estudio_minutos,
    )


if __name__ == "__main__":
    contexto_ejemplo = [
        ChunkResultado(
            texto=(
                "La Virtual Cloud Network (VCN) es una red privada y "
                "personalizable configurada en Oracle Cloud Infrastructure."
            ),
            score=0.95,
            fuente="Introduccion a la Arquitectura de Redes VCN en OCI",
        )
    ]

    try:
        resultado = generar_contenido_adaptado(
            documento_titulo="Introduccion a la Arquitectura de Redes VCN en OCI",
            contexto=contexto_ejemplo,
            perfil_destinatario="Principiante",
            formato_salida="quiz",
            nicho_sector="General",
            nivel_detalle="Didactico",
        )
        print(resultado.model_dump_json(indent=2))
    except ErrorOrquestacion as error:
        print(f"Error: {error}")
