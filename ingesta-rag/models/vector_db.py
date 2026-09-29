"""
Módulo de Persistencia y Operaciones con ChromaDB
Encargado de la indexación vectorial y recuperación de chunks con filtrado por doc_id.
"""

import uuid
import logging
from typing import List
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from schemas.ingesta_schemas import ChunkResultado
from utils.config import CHROMA_PERSIST_DIR, NOMBRE_COLECCION

logger = logging.getLogger(__name__)


def _obtener_vectorstore(embedding_function: Embeddings) -> Chroma:
    """Helper interno para instanciar el cliente ChromaDB."""
    if not embedding_function:
        raise ValueError("Se requiere un objeto de embeddings válido.")

    return Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embedding_function,
        persist_directory=CHROMA_PERSIST_DIR
    )


def indexar_en_chroma(chunks: List[str], documento_titulo: str, embedding_function: Embeddings) -> str:
    """
    Recibe la lista de chunks, genera un doc_id único y los guarda en ChromaDB.

    Retorna:
    - doc_id (str)
    """
    doc_id = str(uuid.uuid4())
    textos = []
    metadatos = []

    for i, texto in enumerate(chunks):
        textos.append(texto)
        metadatos.append({
            "doc_id": doc_id,
            "titulo": documento_titulo,
            "fuente": f"Fragmento {i+1}"
        })

    try:
        vectorstore = _obtener_vectorstore(embedding_function)
        vectorstore.add_texts(texts=textos, metadatas=metadatos)
        logger.info(f"Documento '{documento_titulo}' indexado exitosamente con doc_id: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"Error al indexar en ChromaDB: {str(e)}")
        raise RuntimeError(f"Fallo en la persistencia vectorial: {str(e)}")


def buscar_en_chroma(doc_id: str, query: str, embedding_function: Embeddings, top_k: int = 5) -> List[ChunkResultado]:
    """
    Realiza la búsqueda vectorial de similitud dentro de un documento específico.
    """
    try:
        vectorstore = _obtener_vectorstore(embedding_function)
        resultados_crudos = vectorstore.similarity_search_with_relevance_scores(
            query=query, k=top_k, filter={"doc_id": doc_id}
        )

        resultados_formateados = []
        for doc, score in resultados_crudos:
            resultados_formateados.append(
                ChunkResultado(
                    texto=doc.page_content,
                    score=float(score),
                    fuente=doc.metadata.get("fuente", "Desconocida")
                )
            )
        return resultados_formateados
    except Exception as e:
        logger.error(f"Error al buscar en ChromaDB para doc_id {doc_id}: {str(e)}")
        raise RuntimeError(f"Fallo en la búsqueda de contexto: {str(e)}")