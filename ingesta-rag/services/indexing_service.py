"""
Módulo: services/indexing_service.py
Descripción: Expone la función principal 'indexar_documento' requerida en contratos.txt.
"""

import logging
from services.chunker import dividir_texto
from services.embedding_service import GeminiEmbeddingsResiliente
from models.vector_db import indexar_en_chroma
from utils.key_manager import KeyManager
from utils.config import GEMINI_API_KEYS, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

# Inicialización de servicios desacoplados
_key_manager = KeyManager(keys=GEMINI_API_KEYS)
_embedding_service = GeminiEmbeddingsResiliente(key_manager=_key_manager)


def indexar_documento(documento_titulo: str, documento_contenido: str) -> str:
    """
    Cumple con el contrato: indexar_documento(documento_titulo, documento_contenido) -> str
    """
    print(f"\n[DEBUG-INDEXING] 🚀 Iniciando indexación del documento: '{documento_titulo}'")

    if not documento_contenido or not documento_contenido.strip():
        raise ValueError("El contenido del documento no puede estar vacío.")

    # 1. Chunking
    print("[DEBUG-INDEXING] ✂️  Dividiendo texto en fragmentos (chunking)...")
    chunks = dividir_texto(
        texto=documento_contenido,
        tamano=CHUNK_SIZE,
        solapamiento=CHUNK_OVERLAP
    )

    if not chunks:
        raise ValueError("No se pudieron generar fragmentos del contenido proporcionado.")

    print(f"[DEBUG-INDEXING] 📦 Se generaron {len(chunks)} chunks.")

    # Debugging temporal

    print(f"[DEBUG-INDEXING] Tamaño total del texto: {len(documento_contenido):,} caracteres.")
    print(f"[DEBUG-INDEXING] Chunk más grande: {max(len(c) for c in chunks):,} caracteres.")


    # *****************************************************************************************
    # TEMPORAL
    # *****************************************************************************************
    chunks_grandes = [
        (i, len(chunk))
        for i, chunk in enumerate(chunks)
        if len(chunk) > CHUNK_SIZE
    ]

    print(
        f"[DEBUG-INDEXING] Chunks mayores a {CHUNK_SIZE}: "
        f"{len(chunks_grandes)}"
    )

    for i, longitud in sorted(
        chunks_grandes,
        key=lambda x: x[1],
        reverse=True
    )[:10]:
        print(f"   Chunk {i}: {longitud} caracteres")
    # *****************************************************************************************


    # 2. Embeddings e Indexación
    print("[DEBUG-INDEXING] 💾 Enviando a embeddings e indexando en ChromaDB...")
    doc_id = indexar_en_chroma(
        chunks=chunks,
        documento_titulo=documento_titulo,
        embedding_function=_embedding_service
    )

    print(f"[DEBUG-INDEXING] 🎯 Proceso completado exitosamente. doc_id asignado: {doc_id}\n")
    return doc_id