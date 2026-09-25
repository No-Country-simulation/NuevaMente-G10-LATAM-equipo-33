from shared.contratos import ChunkResultado


def indexar_documento(
    documento_titulo: str,
    documento_contenido: str
) -> str:

    return "mock-doc-001"


def buscar_contexto(
    doc_id: str,
    query: str,
    top_k: int = 5
) -> list[ChunkResultado]:

    return [
        ChunkResultado(
            texto="Contenido técnico de prueba recuperado mediante RAG mock.",
            score=0.95,
            fuente="Documento de prueba - página 1"
        )
    ]