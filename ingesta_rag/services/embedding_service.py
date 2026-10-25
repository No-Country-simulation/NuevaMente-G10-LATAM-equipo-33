"""Embeddings con rotaci?n finita, enfriamiento y cuarentena sin exponer claves."""
from typing import List

from google.genai.types import HttpOptions, HttpRetryOptions
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from ingesta_rag.utils.key_manager import KeyManager
from ingesta_rag.utils.config import MODELO_EMBEDDINGS, MAX_EMBEDDING_ATTEMPTS
from shared.gemini_policy import RotationOperation


class _SingleAttemptEmbeddings(GoogleGenerativeAIEmbeddings):
    def _build_config(self, **kwargs):
        config = super()._build_config(**kwargs)
        # Un intento HTTP total: la pol?tica externa controla las repeticiones.
        config.http_options = HttpOptions(retry_options=HttpRetryOptions(attempts=1))
        return config


class GeminiEmbeddingsResiliente(Embeddings):
    def __init__(self, key_manager: KeyManager, model_name: str = MODELO_EMBEDDINGS):
        self.key_manager = key_manager
        self.model_name = model_name

    def _obtener_instancia_embeddings(self, api_key=None):
        return _SingleAttemptEmbeddings(
            model=self.model_name.replace("models/", "").strip(),
            google_api_key=api_key if api_key is not None else self.key_manager.obtener_key_activa(),
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        operation = RotationOperation(self.key_manager, max_attempts=MAX_EMBEDDING_ATTEMPTS)
        vectors = []
        successes = 0
        # Misma partici?n de LangChain: cada lote externo genera una sola petici?n,
        # sin repetir sublotes ya completados si el proveedor falla posteriormente.
        for batch in _SingleAttemptEmbeddings._prepare_batches(texts, 50):
            def invoke(key):
                return self._obtener_instancia_embeddings(key).embed_documents(batch, batch_size=50)
            vectors.extend(operation.run(invoke))
            successes += 1
            if successes >= 2:
                self.key_manager._rotar_siguiente()
                successes = 0
        return vectors

    def embed_query(self, text: str) -> List[float]:
        operation = RotationOperation(self.key_manager, max_attempts=MAX_EMBEDDING_ATTEMPTS)
        return operation.run(lambda key: self._obtener_instancia_embeddings(key).embed_query(text))
