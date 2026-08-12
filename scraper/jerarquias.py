"""Jerarquías de plataformas del scraper (fuente única de verdad).

Centraliza los órdenes de preferencia entre plataformas para no duplicarlos
en varios módulos. Documentación completa en `docs/scraping.md`.

Hay dos jerarquías distintas (no confundir):
- Foto de perfil (`PRIORIDAD_FOTO_DE_PERFIL`): de qué plataforma se toma la
  URL de la foto de perfil de un artista cuando hay varias disponibles.
- Enlace puente (`PRIORIDAD_LINK_PUENTE`): qué enlace se muestra como
  "principal" en la tarjeta de un artista cuando hay varios disponibles.
"""

# Foto de perfil: orden de preferencia entre plataformas.
PRIORIDAD_FOTO_DE_PERFIL = [
    "spotify",
    "bandcamp",
    "soundcloud",
    "yt",
    "ig",
    "fb",
    "tt",
    "x",
]

# Enlace "puente" (principal) de la tarjeta de artista.
PRIORIDAD_LINK_PUENTE = ["yt", "spotify", "bandcamp", "soundcloud", "ig", "tt", "web"]
