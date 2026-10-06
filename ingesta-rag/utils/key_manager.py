"""
Módulo: utils/key_manager.py
Descripción: Administrador y rotador de API Keys para Google Gemini.
Garantiza tolerancia a fallos por límites de cuota (Rate Limit / Quota Exceeded).
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Gestiona un pool de API Keys de Gemini y permite rotar automáticamente
    cuando una clave falla o supera su cuota.
    """

    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("Se requiere al menos una API Key de Gemini válida.")

        self.keys_pool: List[str] = [k.strip() for k in keys if k and k.strip()]
        if not self.keys_pool:
            raise ValueError("El pool de API Keys no contiene claves válidas.")

        self._indice_actual: int = 0
        self._keys_invalidas: set[str] = set()

    def obtener_key_activa(self) -> str:
        """Devuelve la API Key actualmente operativa."""
        if len(self._keys_invalidas) >= len(self.keys_pool):
            logger.warning("Todas las API Keys en el pool han sido marcadas como inválidas. Reiniciando pool de keys inválidas.")
            self._keys_invalidas.clear()

        key = self.keys_pool[self._indice_actual]
        while key in self._keys_invalidas:
            self._rotar_siguiente()
            key = self.keys_pool[self._indice_actual]

        return key

    def _rotar_siguiente(self) -> str:
        """Avanza al siguiente índice disponible en el pool."""
        self._indice_actual = (self._indice_actual + 1) % len(self.keys_pool)
        return self.keys_pool[self._indice_actual]

    def rotar_a_siguiente_valida(self) -> str:
        """Fuerza la rotación a la siguiente API Key válida disponible."""
        self._rotar_siguiente()
        return self.obtener_key_activa()

    def marcar_key_invalida(self, key: str, razon: Optional[str] = None) -> str:
        """
        Marca una API Key como no disponible temporalmente y conmuta
        a la siguiente disponible.
        """
        logger.warning(f"Marcando API Key (...{key[-4:] if len(key) >= 4 else key}) como inválida. Razón: {razon}")
        self._keys_invalidas.add(key)
        return self._rotar_siguiente()