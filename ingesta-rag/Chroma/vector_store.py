import uuid
import logging
from pydantic import BaseModel
from langchain_chroma import Chroma

# Contrato de salida para la búsqueda
class ChunkResultado(BaseModel):
    texto: str
    score: float
    fuente: str

# Configuración interna
CHROMA_PERSIST_DIR = "./chroma_db"
NOMBRE_COLECCION = "nuevamente_documentos"
_funcion_embeddings = None

def configurar_motor_rag(funcion_embeddings):
    """Inicializa el motor de embeddings para LangChain Chroma."""
    global _funcion_embeddings
    if funcion_embeddings is None:
        raise ValueError("Se requiere una función de embeddings válida.")
    _funcion_embeddings = funcion_embeddings

def _obtener_vectorstore() -> Chroma:
    if not _funcion_embeddings:
        raise ValueError("La función de embeddings no ha sido inicializada.")
    return Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=_funcion_embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )

# Módulo exportable

def indexar_en_chroma(chunks: list[str], documento_titulo: str) -> str:
    """
    Recibe los chunks limpios y los guarda en ChromaDB.
   
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
        vectorstore = _obtener_vectorstore()
        vectorstore.add_texts(texts=textos, metadatas=metadatos)
        return doc_id
    except Exception as e:
        logging.error(f"Error al indexar en Chroma: {str(e)}")
        raise RuntimeError(f"Fallo en la persistencia vectorial: {str(e)}")


def buscar_en_chroma(doc_id: str, query: str, top_k: int = 5) -> list[ChunkResultado]:
    """
    búsqueda vectorial.
    """
    vectorstore = _obtener_vectorstore()
    resultados_crudos = vectorstore.similarity_search_with_relevance_scores(
        query=query, k=top_k, filter={"doc_id": doc_id}
    )
    
    resultados_formateados = []
    for doc, score in resultados_crudos:
        resultados_formateados.append(
            ChunkResultado(texto=doc.page_content, score=score, fuente=doc.metadata.get("fuente", "Desconocida"))
        )
    return resultados_formateados
