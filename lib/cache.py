"""Caché en memoria con TTL para la API.

Implementación mínima, sin dependencias externas. En un futuro se puede
sustituir por Redis/Upstash manteniendo la misma interfaz pública.
"""

from __future__ import annotations

import threading
import time
from typing import Any


class MemoryCache:
    """Caché key-value con expiración por TTL (segundos).

    Thread-safe mediante un lock. Pensado para lecturas públicas que no
    cambian entre sincronizaciones. Las escrituras invalidan las claves
    que correspondan.
    """

    def __init__(self) -> None:
        self._datos: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def _ahora(self) -> float:
        return time.monotonic()

    def get(self, key: str) -> Any | None:
        with self._lock:
            valor, expira = self._datos.get(key, (None, 0.0))
            if expira and expira < self._ahora():
                self._datos.pop(key, None)
                return None
            return valor

    def set(self, key: str, valor: Any, ttl: int) -> None:
        with self._lock:
            self._datos[key] = (valor, self._ahora() + ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._datos.pop(key, None)

    def delete_pattern(self, prefix: str) -> None:
        """Elimina todas las claves que empiecen con `prefix`."""
        with self._lock:
            for key in list(self._datos.keys()):
                if key.startswith(prefix):
                    self._datos.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._datos.clear()


# Instancia compartida para la API. Se puede reemplazar fácilmente por una
# conexión a Redis sin modificar los consumidores.
_default_cache = MemoryCache()


def get_cache() -> MemoryCache:
    """Devuelve la caché por defecto de la aplicación."""
    return _default_cache
