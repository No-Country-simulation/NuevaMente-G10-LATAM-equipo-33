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
  ErrorGeneracion     falló la generación con Gemini
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

from shared.contratos import (
    ChunkResultado,
    ContenidoGenerado,
    ContenidoFlashcards,
    ContenidoQuiz,
)

load_dotenv()
logger = logging.getLogger(__name__)

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

NICHO_POR_DEFECTO = "General"
NIVEL_DETALLE_POR_DEFECTO = "Didactico"


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
"""


def _obtener_api_key() -> str | None:
    """Acepta GOOGLE_API_KEY / GEMINI_API_KEY o la primera de GEMINI_API_KEYS."""
    clave = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if clave:
        return clave
    claves = [c.strip() for c in os.getenv("GEMINI_API_KEYS", "").split(",") if c.strip()]
    return claves[0] if claves else None


@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    """Crea el LLM la primera vez que se usa (así importar el módulo no exige API key)."""
    api_key = _obtener_api_key()
    if not api_key:
        raise ErrorGeneracion(
            "Falta configurar la API key de Gemini "
            "(GEMINI_API_KEYS, GEMINI_API_KEY o GOOGLE_API_KEY)."
        )
    return ChatGoogleGenerativeAI(
        model=MODELO,
        google_api_key=api_key,
        temperature=0.3,
        max_retries=3,
    )


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
    )

    try:
        llm_estructurado = _get_llm().with_structured_output(modelo_formato)
        resultado_tipado = llm_estructurado.invoke(prompt)
    except ErrorGeneracion:
        raise
    except Exception as error:
        logger.warning("Falló la generación con Gemini: %s", error)
        raise ErrorGeneracion(
            f"No se pudo generar el contenido con Gemini ({type(error).__name__}). "
            "Intentá de nuevo en unos minutos."
        ) from error

    if resultado_tipado is None or not resultado_tipado.items:
        raise ErrorGeneracion("Gemini devolvió un contenido vacío. Intentá de nuevo.")

    # Normaliza al contrato genérico: items pasa de objetos tipados
    # (ItemFlashcard/ItemQuiz) a dict[str, Any] plano.
    return ContenidoGenerado(
        titulo=resultado_tipado.titulo,
        introduccion_contextualizada=resultado_tipado.introduccion_contextualizada,
        items=[item.model_dump() for item in resultado_tipado.items],
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