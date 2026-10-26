"""
Módulo: utils/key_manager.py
Descripción: Administrador y rotador de API Keys para Google Gemini.
Garantiza tolerancia a fallos por límites de cuota (Rate Limit / Quota Exceeded).
"""

import logging
import time
from typing import List, Optional

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Gestiona un pool de API Keys de Gemini y permite rotar automáticamente
    cuando una clave falla o supera su cuota.
    """

    def __init__(self, keys: List[str], *, quarantine_seconds=60.0, clock=None):
        if not keys:
            raise ValueError("Se requiere al menos una API Key de Gemini válida.")

        self.keys_pool: List[str] = list(dict.fromkeys(k.strip() for k in keys if k and k.strip()))
        if not self.keys_pool:
            raise ValueError("El pool de API Keys no contiene claves válidas.")

        self._indice_actual: int = 0
        self._keys_invalidas: set[str] = set()
        self.quarantine_seconds = quarantine_seconds
        self.clock = time.monotonic if clock is None else clock
        self._quarantine_until = {}
        self._429_streak = {}
        self._last_429_round = {}
        self._round = 0
        self._round_seen = set()

    def obtener_key_activa(self, excluidas=None) -> str:
        """Devuelve la API Key actualmente operativa."""
        excluidas = excluidas or set()
        for _ in self.keys_pool:
            key = self.keys_pool[self._indice_actual]
            until = self._quarantine_until.get(key)
            if until is not None and self.clock() >= until:
                del self._quarantine_until[key]
                self.registrar_exito(key)  # Nueva ventana de prueba al terminar la cuarentena.
            if key not in self._keys_invalidas and key not in excluidas and key not in self._quarantine_until:
                return key
            self._rotar_siguiente()
        raise RuntimeError("No hay claves disponibles fuera de exclusión o cuarentena.")

    def iniciar_ronda(self):
        """Una ronda es una pasada por claves disponibles, también entre operaciones."""
        self._round += 1
        self._round_seen.clear()

    def registrar_intento(self, key):
        if self._round == 0 or key in self._round_seen:
            self.iniciar_ronda()
        self._round_seen.add(key)

    def registrar_429(self, key):
        previous = self._last_429_round.get(key)
        if previous == self._round:
            return
        self._429_streak[key] = self._429_streak.get(key, 0) + 1 if previous == self._round - 1 else 1
        self._last_429_round[key] = self._round
        if self._429_streak[key] >= 3:
            self._quarantine_until[key] = self.clock() + self.quarantine_seconds
            logger.warning("Clave en cuarentena temporal tras tres rondas consecutivas con 429.")

    def registrar_exito(self, key):
        self._429_streak.pop(key, None)
        self._last_429_round.pop(key, None)

    def registrar_otro_error(self, key):
        self.registrar_exito(key)

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
        logger.warning("Clave marcada como no disponible; detalles externos omitidos.")
        self._keys_invalidas.add(key)
        return self._rotar_siguiente()
