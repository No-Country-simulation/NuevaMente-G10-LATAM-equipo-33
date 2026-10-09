"""
Módulo: services/ingestion.py
Descripción: Interfaz principal del módulo de ingesta (RAG).
Expone las funciones requeridas por el contrato para comunicarse con
'orquestacion-agentes' y el backend, orquestando los servicios internos.
"""

import logging

# Importamos las estructuras de datos definidas en el contrato unificado
# (Asumiendo que el archivo de contratos se llama contratos.py)
from contratos import ChunkResultado

# Importamos los servicios internos que ya construimos
from services.indexing_service import indexar_documento as _indexar_impl
from services.embedding_service import GeminiEmbeddingsResiliente

logger = logging.getLogger(__name__)

def indexar_documento(documento_titulo: str, documento_contenido: str) -> str:
    """
    Cumple con el Contrato 1: Chunkea, genera embeddings, e indexa en el vector store.

    Delega la lógica pesada a indexing_service.py para mantener el monolito modular.
    """

    # Evidencia de Entrada
    print(f"\n[INGESTION - ENTRADA indexar_documento]")
    print(f" └─ documento_titulo: '{documento_titulo}'")
    print(f" └─ documento_contenido: {len(documento_contenido)} caracteres")

    logger.info(f"[INGESTION] Recibiendo petición de backend para indexar: '{documento_titulo}'")

    # Delegamos al servicio de indexación previamente definido
    doc_id = _indexar_impl(
        documento_titulo=documento_titulo,
        documento_contenido=documento_contenido
    )

    # Evidencia de Salida
    print(f"[INGESTION - SALIDA indexar_documento]")
    print(f" └─ doc_id asignado: '{doc_id}'\n")

    return doc_id

