"""Regla de actividad y utilidades de cálculo (espejo de ESCENA_LOCAL.md)."""

from datetime import date, timedelta

REGLA_ACTIVIDAD = (
    "activo = señal de actividad (lanzamiento, evento o elemento del feed) "
    "en los últimos 6 meses; en_duda = señal entre 6 y 18 meses o sin señal "
    "conocida; inactivo = sin señal en más de 18 meses o pausa confirmada. "
    "Se usa la señal más reciente de todas las disponibles."
)

DIAS_ACTIVO = 182  # ~6 meses
DIAS_EN_DUDA = 548  # ~18 meses


def estado_activo_recomputado(
    artista, hoy: date | None = None, ultimo_feed: date | None = None
) -> str:
    """Recalcula `estado_activo` de un artista según la regla documentada.

    `artista` debe tener: `metodo_actividad`, `ultimo_lanzamiento`,
    `ultimo_evento`. `ultimo_feed` es la fecha del elemento más reciente del
    feed del artista. Se toma como referencia la **señal más reciente** de
    todas (lanzamiento, evento o feed).
    """
    hoy = hoy or date.today()

    if artista.metodo_actividad == "artista (EN PAUSA)":
        return "inactivo"
    if artista.metodo_actividad in ("lanzamiento_próximo", "presencia_continua"):
        return "activo"

    candidatas = [
        d for d in (artista.ultimo_lanzamiento, artista.ultimo_evento, ultimo_feed)
        if d is not None
    ]
    if not candidatas:
        return "en_duda"
    referencia = max(candidatas)

    dias = (hoy - referencia).days
    if dias <= DIAS_ACTIVO:
        return "activo"
    if dias <= DIAS_EN_DUDA:
        return "en_duda"
    return "inactivo"


def dias_desde(fecha: date | None, hoy: date | None = None) -> int | None:
    if fecha is None:
        return None
    hoy = hoy or date.today()
    return (hoy - fecha).days


def ultimo_referencia(artista) -> date | None:
    """Última señal de actividad (lanzamiento o evento)."""
    return artista.ultimo_lanzamiento or artista.ultimo_evento
