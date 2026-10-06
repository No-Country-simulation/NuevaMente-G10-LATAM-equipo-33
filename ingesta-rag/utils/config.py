import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. GEMINI - API KEYS
# ==========================================
_keys_raw = os.getenv("GEMINI_API_KEYS", "")

GEMINI_API_KEYS = [
    k.strip()
    for k in _keys_raw.split(",")
    if k.strip()
]

if not GEMINI_API_KEYS:
    raise ValueError(
        "No se encontraron API Keys en GEMINI_API_KEYS."
    )


# ==========================================
# 2. GEMINI - MODELO DE EMBEDDINGS
# ==========================================
MODELO_EMBEDDINGS = os.getenv(
    "MODELO_EMBEDDINGS",
    "gemini-embedding-001"
)


# ==========================================
# 3. CHUNKING
# ==========================================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

if CHUNK_SIZE <= 0:
    raise ValueError("CHUNK_SIZE debe ser mayor que cero.")

if CHUNK_OVERLAP < 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
    raise ValueError(
        "CHUNK_OVERLAP debe ser mayor o igual a cero "
        "y menor que CHUNK_SIZE."
    )


# ==========================================
# 4. CHROMADB
# ==========================================
CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    "./chroma_db"
)

NOMBRE_COLECCION = os.getenv(
    "NOMBRE_COLECCION",
    "nuevamente_documentos"
)