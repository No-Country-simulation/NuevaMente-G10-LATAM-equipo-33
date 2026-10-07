import sys
from pathlib import Path

# Resolver la ruta hacia la carpeta 'ingesta-rag'
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAG_DIR = BASE_DIR / "ingesta-rag"

if str(RAG_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DIR))

# Importación de las funciones reales desde ingesta-rag
from services.ingestion import indexar_documento
from services.retrieving_service import buscar_contexto

__all__ = ["indexar_documento", "buscar_contexto"]