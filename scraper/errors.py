"""Excepciones comunes del scraper.

Jerarquía única: los adaptadores lanzan subclases de `ScraperError` para que
quien los use (scripts, servicios) pueda atrapar todos los fallos de scraping
con un solo `except`.
"""


class ScraperError(RuntimeError):
    """Error base de los adaptadores de scraping."""