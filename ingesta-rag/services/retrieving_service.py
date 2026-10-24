"""
Servicio de recuperación de contexto RAG.

Expone una interfaz simple para backend/orquestación.
"""

from typing import List

from models.vector_db import buscar_en_chroma
from contratos import ChunkResultado    # Importación de los Contratos
from services.embedding_service import GeminiEmbeddingsResiliente
from utils.key_manager import KeyManager
from utils.config import GEMINI_API_KEYS


# Servicio compartido de embeddings
_key_manager = KeyManager(keys=GEMINI_API_KEYS)

_embedding_service = GeminiEmbeddingsResiliente(
    key_manager=_key_manager
)


def buscar_contexto(
    doc_id: str,
    query: str,
    top_k: int = 5
) -> List[ChunkResultado]:
    """
    Busca fragmentos relevantes dentro de un documento indexado.

    Parámetros:
    - doc_id: identificador del documento indexado.
    - query: pregunta o texto de búsqueda.
    - top_k: cantidad máxima de fragmentos.

    Retorna:
    - Lista de ChunkResultado.
    """

    # --- Evidencia de ENTRADA ---
    print(f"\n[ENTRADA - buscar_contexto]")
    print(f" └─ doc_id: '{doc_id}'")
    print(f" └─ query: '{query}'")
    print(f" └─ top_k: {top_k}")

    if not doc_id:
        raise ValueError(
            "doc_id no puede estar vacío."
        )

    if not query:
        raise ValueError(
            "query no puede estar vacío."
        )


    resultados = buscar_en_chroma(
        doc_id=doc_id,
        query=query,
        embedding_function=_embedding_service,
        top_k=top_k
    )

    # --- Evidencia de SALIDA ---
    print(f"[SALIDA - buscar_contexto]")
    print(f" └─ Objetos ChunkResultado retornados ({len(resultados)}):")
    for i, chunk in enumerate(resultados, 1):
        score_val = getattr(chunk, 'score', 0.0)
        fuente_val = getattr(chunk, 'fuente', 'N/A')
        texto_val = getattr(chunk, 'texto', '')
        print(f" [{i}] Score: {score_val:.4f} | Fuente: {fuente_val}")
        print(f" Texto: {texto_val[:120]}...\n")

    return resultados