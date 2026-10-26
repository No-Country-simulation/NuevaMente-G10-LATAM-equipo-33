
"""Adaptador del backend hacia el módulo real de ingesta-rag."""

from shared.contratos import ChunkResultado

from ingesta_rag.services.ingestion import (
    indexar_documento as _indexar_documento,
)
from ingesta_rag.services.retrieving_service import (
    buscar_contexto as _buscar_contexto,
)

from backend.core.exceptions import RagError


def indexar(
    titulo: str,
    contenido: str,
) -> str:
    """Indexa el documento mediante el RAG real."""

    try:
        doc_id = _indexar_documento(
            documento_titulo=titulo,
            documento_contenido=contenido,
        )

        if not doc_id:
            raise RagError(
                "El módulo RAG no devolvió un identificador."
            )

        return doc_id

    except RagError:
        raise
    except Exception as exc:
        raise RagError(
            "No fue posible indexar el documento."
        ) from exc


def buscar(
    doc_id: str,
    query: str,
    top_k: int = 5,
) -> list[ChunkResultado]:
    """Recupera fragmentos del documento mediante el RAG real."""

    try:
        resultados = _buscar_contexto(
            doc_id=doc_id,
            query=query,
            top_k=top_k,
        )

        # Comprobar que los resultados cumplen el contrato compartido.
        return [
            chunk
            if isinstance(chunk, ChunkResultado)
            else ChunkResultado.model_validate(chunk)
            for chunk in resultados
        ]

    except RagError:
        raise
    except Exception as exc:
        raise RagError(
            "No fue posible recuperar el contexto del documento."
        ) from exc
