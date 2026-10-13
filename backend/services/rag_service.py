class RagService:

    def indexar(self, titulo: str, contenido: str) -> str:
        ...

    def buscar(self, doc_id: str, query: str, top_k: int = 5):
        ...