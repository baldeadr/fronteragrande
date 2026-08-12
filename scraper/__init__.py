"""Motor de scraping de actividad para la escena local.

El objetivo es detectar si un proyecto está activo a partir de su huella
en internet (URLs vivas, plataformas de streaming, redes sociales).
"""

from scraper.core import estado_activo_recomputado, REGLA_ACTIVIDAD

__all__ = ["estado_activo_recomputado", "REGLA_ACTIVIDAD"]
