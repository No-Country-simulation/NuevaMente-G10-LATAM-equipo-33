"""
Módulo: services/embedding_service.py
Descripción: Servicio de Generación de Embeddings utilizando Google Gemini.
Incorpora rotación preventiva por número de lotes (máximo 2 lotes por Key)
y pausas inteligentes ante límites de tasa (429/RPM) con tiempo mínimo garantizado.
"""

import logging
import re
import time
from typing import List
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from utils.key_manager import KeyManager
from utils.config import MODELO_EMBEDDINGS

logger = logging.getLogger(__name__)

# Tiempo de enfriamiento estándar y mínimo garantizado
TIEMPO_ENFRIAMIENTO_RPM_DEFECTO = 60
PAUSA_MINIMA_RPM = 30  # Asegura un margen de enfriamiento real antes de reanudar


class GeminiEmbeddingsResiliente(Embeddings):
    """
    Wrapper de GoogleGenerativeAIEmbeddings que añade tolerancia a fallos,
    pausas inteligentes y rotación preventiva tras N lotes procesados.
    """
    def __init__(self, key_manager: KeyManager, model_name: str = MODELO_EMBEDDINGS):
        self.key_manager = key_manager
        self.model_name = model_name

    def _obtener_instancia_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Instancia la clase de LangChain con la API Key activa."""
        api_key_activa = self.key_manager.obtener_key_activa()

        # Limpieza de seguridad para evitar duplicaciones del tipo 'models/models/text-embedding-004'
        nombre_limpio = self.model_name.replace("models/", "").strip()

        return GoogleGenerativeAIEmbeddings(
            model=nombre_limpio,
            google_api_key=api_key_activa
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings de documentos procesando en lotes (batching),
        rotando de API Key preventivamente cada 2 lotes exitosos.
        """
        print(f"   [DEBUG-EMBEDDINGS] Generando embeddings para {len(texts)} chunks en lotes...")

        if not texts:
            return []

        BATCH_SIZE = 50  # Mantenemos 50 chunks por llamada para ahorrar cuota diaria (RPD)
        PAUSA_ENTRE_LOTES = 1.0  # Pausa ligera entre llamadas
        MAX_FALLOS_CONSECUTIVOS_RPM = 2
        MAX_LOTES_POR_KEY = 2  # Regla: Máximo 2 lotes por API Key antes de rotar

        vectores: List[List[float]] = []
        total_lotes = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

        lotes_consecutivos_key = 0  # Contador de lotes procesados por la Key actual

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            num_lote = (i // BATCH_SIZE) + 1

            fallos_consecutivos_429 = 0
            lote_completado = False

            while not lote_completado:
                api_key_activa = self.key_manager.obtener_key_activa()
                print(
                    f"   [DEBUG-EMBEDDINGS] Procesando lote {num_lote}/{total_lotes} "
                    f"({len(batch)} chunks) con Key: ...{api_key_activa[-4:]} "
                    f"[Lote {lotes_consecutivos_key + 1}/{MAX_LOTES_POR_KEY} para esta Key]"
                )
                instancia = self._obtener_instancia_embeddings()

                try:
                    vectores_lote = instancia.embed_documents(batch)
                    vectores.extend(vectores_lote)

                    print(
                        f"   [DEBUG-EMBEDDINGS] ✅ Lote {num_lote}/{total_lotes} "
                        f"procesado con éxito. Total acumulado: {len(vectores)}/{len(texts)}"
                    )
                    lote_completado = True
                    fallos_consecutivos_429 = 0  # Reiniciar contador de fallos tras éxito
                    lotes_consecutivos_key += 1

                    # Si la key actual ya procesó 2 lotes, rotamos a la siguiente preventivamente
                    if lotes_consecutivos_key >= MAX_LOTES_POR_KEY:
                        print(
                            f"   [DEBUG-EMBEDDINGS] 🔄 Key ...{api_key_activa[-4:]} alcanzó el límite de "
                            f"{MAX_LOTES_POR_KEY} lotes seguidos. Rotando preventivamente a la siguiente Key..."
                        )
                        self.key_manager.rotar_a_siguiente_valida()
                        lotes_consecutivos_key = 0  # Reiniciar contador para la nueva key

                except Exception as e:
                    mensaje = str(e)
                    es_cuota = (
                        "RESOURCE_EXHAUSTED" in mensaje
                        or "429" in mensaje
                        or "quota exceeded" in mensaje.lower()
                    )

                    if not es_cuota:
                        logger.error(f"Error crítico no relacionado con cuotas en lote {num_lote}: {mensaje}")
                        raise RuntimeError(f"Error fatal al generar embeddings en lote {num_lote}: {mensaje}") from e

                    fallos_consecutivos_429 += 1
                    lotes_consecutivos_key = 0  # Si falla, reiniciamos el conteo de la key
                    print(
                        f"   [DEBUG-EMBEDDINGS] ⚠️ Cuota/RPM alcanzada en Key ...{api_key_activa[-4:]} "
                        f"(Fallo consecutivo {fallos_consecutivos_429})."
                    )

                    # Si 2 keys consecutivas fallan por 429, hacer pausa de enfriamiento con tiempo mínimo garantizado
                    if fallos_consecutivos_429 >= MAX_FALLOS_CONSECUTIVOS_RPM:
                        coincidencia = re.search(
                            r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+)(?:s)?",
                            mensaje,
                            re.IGNORECASE
                        )
                        espera_detectada = int(coincidencia.group(1)) if coincidencia else TIEMPO_ENFRIAMIENTO_RPM_DEFECTO

                        # Garantizamos al menos PAUSA_MINIMA_RPM segundos
                        espera = max(espera_detectada, PAUSA_MINIMA_RPM)

                        print(
                            f"   [DEBUG-EMBEDDINGS] ⏳ {fallos_consecutivos_429} API Keys consecutivas agotadas por RPM. "
                            f"Pausando ejecución {espera} segundos para liberar cuota..."
                        )
                        time.sleep(espera)
                        fallos_consecutivos_429 = 0

                    # Rotar a la siguiente API Key para el reintento
                    self.key_manager.rotar_a_siguiente_valida()

            # Pausa ligera entre lotes
            if i + BATCH_SIZE < len(texts):
                time.sleep(PAUSA_ENTRE_LOTES)

        print(f"   [DEBUG-EMBEDDINGS] 🎉 Vectores generados exitosamente ({len(vectores)} vectores obtenidos).")
        return vectores

    def embed_query(self, text: str) -> List[float]:
        """Genera el vector de embedding para una consulta individual."""
        print(f"   [DEBUG-EMBEDDINGS] Generando embedding para consulta: '{text[:30]}...'")
        intentos = len(self.key_manager.keys_pool)

        for intento in range(intentos):
            key_actual = self.key_manager.obtener_key_activa()
            try:
                instancia = self._obtener_instancia_embeddings()
                vector = instancia.embed_query(text)
                print(f"   [DEBUG-EMBEDDINGS] ✅ Vector de consulta generado con dimensión: {len(vector)}")
                return vector
            except Exception as e:
                print(f"   [DEBUG-EMBEDDINGS] ❌ Error en intento {intento+1}: {str(e)}")
                logger.error(f"Error al generar embedding de la consulta (intento {intento+1}): {str(e)}")
                self.key_manager.marcar_key_invalida(key_actual, razon=str(e))

        raise RuntimeError("Todas las API Keys de Gemini fallaron durante el embedding de la consulta.")