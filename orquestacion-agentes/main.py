"""
Módulo orquestacion-agentes — NuevaMente

Recibe el contexto recuperado por ingesta-rag y, vía Gemini, genera el
contenido adaptado según perfil, formato y nicho solicitados.

Implementa el contrato definido en shared/contratos.py:
  entrada:  list[ChunkResultado]  (viene de ingesta-rag)
  salida:   ContenidoGenerado     (va hacia backend)
"""

import os
import sys
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

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.3,
    max_retries=3,
)

# Mapeo formato_salida -> modelo Pydantic tipado que fuerza la estructura
# correcta de "items" para ese formato específico.
MODELOS_POR_FORMATO = {
    "Flashcards": ContenidoFlashcards,
    "Quiz": ContenidoQuiz,
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


def generar_contenido_adaptado(
    documento_titulo: str,
    contexto: list[ChunkResultado],
    perfil_destinatario: str,
    formato_salida: str,
    nicho_sector: str,
    nivel_detalle: str,
) -> ContenidoGenerado:
    modelo_formato = MODELOS_POR_FORMATO.get(formato_salida)
    if modelo_formato is None:
        raise ValueError(
            f"Formato '{formato_salida}' no soportado. "
            f"Formatos disponibles: {list(MODELOS_POR_FORMATO.keys())}"
        )

    contexto_texto = "\n\n".join(
        f"[Fuente: {c.fuente} | relevancia: {c.score:.2f}]\n{c.texto}"
        for c in contexto
    )

    prompt = PROMPT_TEMPLATE.format(
        documento_titulo=documento_titulo,
        contexto_texto=contexto_texto,
        perfil_destinatario=perfil_destinatario,
        formato_salida=formato_salida,
        nicho_sector=nicho_sector,
        nivel_detalle=nivel_detalle,
    )

    llm_estructurado = llm.with_structured_output(modelo_formato)
    resultado_tipado = llm_estructurado.invoke(prompt)

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

    resultado = generar_contenido_adaptado(
        documento_titulo="Introduccion a la Arquitectura de Redes VCN en OCI",
        contexto=contexto_ejemplo,
        perfil_destinatario="Principiante",
        formato_salida="Quiz",
        nicho_sector="General",
        nivel_detalle="Didactico",
    )
    print(resultado.model_dump_json(indent=2))