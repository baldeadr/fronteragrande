"""Clasificación del `genero_dominante` a partir de los subgéneros.

Protege la taxonomía de los 10 géneros dominantes (Regional, Rock,
Metal, Urbano, EDM, Dark, Pop, Cumbia, Roots, Experimental) y el cálculo
automático en `lib.helpers.clasificar_genero_dominante`.
"""

from lib.helpers import (
    EXCEPCIONES_GENERO_DOMINANTE,
    GENEROS_DOMINANTES,
    clasificar_genero_dominante,
)


def test_diez_generos_dominantes():
    assert GENEROS_DOMINANTES == [
        "Regional",
        "Rock",
        "Metal",
        "Urbano",
        "EDM",
        "Dark",
        "Pop",
        "Cumbia",
        "Roots",
        "Experimental",
    ]


def test_regional():
    assert clasificar_genero_dominante("x", "cumbia norteña/regional mexicano") == "Regional"
    assert clasificar_genero_dominante("x", "norteño") == "Regional"
    assert clasificar_genero_dominante("x", "mariachi/conjunto") == "Regional"
    assert clasificar_genero_dominante("x", "polka") == "Regional"
    assert clasificar_genero_dominante("x", "tejano/tex-mex") == "Regional"


def test_rock():
    assert clasificar_genero_dominante("x", "rock alternativo") == "Rock"
    assert clasificar_genero_dominante("x", "pop punk/emo/punk rock") == "Rock"
    assert clasificar_genero_dominante("x", "garage rock, rock alternativo") == "Rock"
    assert clasificar_genero_dominante("x", "indie/shoegaze/dreampop") == "Rock"
    assert clasificar_genero_dominante("x", "alternativo") == "Rock"
    assert clasificar_genero_dominante("x", "psychedelic/stoner") == "Rock"


def test_metal():
    assert clasificar_genero_dominante("x", "death metal") == "Metal"
    assert clasificar_genero_dominante("x", "nu metal/alternative metal") == "Metal"
    assert clasificar_genero_dominante("x", "electronicore/metalcore") == "Metal"


def test_urbano():
    assert clasificar_genero_dominante("x", "hip hop/rap/trap") == "Urbano"
    assert clasificar_genero_dominante("x", "rap") == "Urbano"
    assert clasificar_genero_dominante("x", "narco rap/hip hop/corridos tumbados/trap") == "Urbano"
    assert clasificar_genero_dominante("x", "reggaetón/trap") == "Urbano"
    assert clasificar_genero_dominante("x", "trap/urbano") == "Urbano"


def test_edm():
    assert clasificar_genero_dominante("x", "house/techno") == "EDM"
    assert clasificar_genero_dominante("x", "electronic/bass house") == "EDM"
    assert clasificar_genero_dominante("x", "drum and bass") == "EDM"
    assert clasificar_genero_dominante("x", "deep house/trance") == "EDM"


def test_dark():
    assert clasificar_genero_dominante("x", "post-punk / coldwave / darkwave") == "Dark"
    assert clasificar_genero_dominante("x", "darkwave") == "Dark"
    assert clasificar_genero_dominante("x", "industrial/darkwave") == "Dark"
    assert clasificar_genero_dominante("x", "gothic rock") == "Dark"
    assert clasificar_genero_dominante("x", "electrónica / industrial / tecnodark") == "Dark"
    assert clasificar_genero_dominante("x", "synthwave") == "Dark"


def test_pop():
    assert clasificar_genero_dominante("x", "pop") == "Pop"
    assert clasificar_genero_dominante("x", "latin pop") == "Pop"
    assert clasificar_genero_dominante("x", "pop romantico") == "Pop"


def test_cumbia_y_tropical():
    assert clasificar_genero_dominante("x", "cumbia / villero") == "Cumbia"
    assert clasificar_genero_dominante("x", "cumbia/tropical") == "Cumbia"
    assert clasificar_genero_dominante("x", "afrobeat/world music") == "Cumbia"


def test_roots():
    assert clasificar_genero_dominante("x", "blues") == "Roots"
    assert clasificar_genero_dominante("x", "trova/rock/blues/jazz") == "Roots"
    assert clasificar_genero_dominante("x", "country") == "Roots"
    assert clasificar_genero_dominante("x", "americana/bluegrass") == "Roots"


def test_sin_clasificar():
    assert clasificar_genero_dominante("x", "[PENDIENTE]") == ""
    assert clasificar_genero_dominante("x", "") == ""


def test_experimental():
    assert clasificar_genero_dominante("x", "noise/experimental") == "Experimental"
    assert clasificar_genero_dominante("x", "electronic drone / hyperpop industrial") == "Experimental"
    assert clasificar_genero_dominante("x", "vanguardia") == "Experimental"
    assert clasificar_genero_dominante("x", "avant-garde / darkwave") == "Experimental"
    assert clasificar_genero_dominante("x", "triphop/ambient") == "Experimental"
    # El noise rock conserva su base rock aunque exista "noise".
    assert clasificar_genero_dominante("x", "noise rock/dreampop") == "Rock"


def test_excepciones_editoriales():
    assert EXCEPCIONES_GENERO_DOMINANTE["apex_ultra"] == "Dark"
    assert clasificar_genero_dominante("apex_ultra", "Rock, Electronica, Industrial, Drum and Bass") == "Dark"
    assert clasificar_genero_dominante("angelic_oz", "hyperpop/reggaeton triste/cybercore") == "Urbano"
    assert clasificar_genero_dominante("de_regreso_a_nocheosfera", "indie/shoegaze/noise rock/dreampop") == "Dark"
    assert EXCEPCIONES_GENERO_DOMINANTE["distraught"] == "Dark"
    assert clasificar_genero_dominante("distraught", "industrial metal / techno / acid") == "Dark"


def test_jonathan_kaz_clasifica_solo():
    assert "jonathan_kaz" not in EXCEPCIONES_GENERO_DOMINANTE
    assert clasificar_genero_dominante("jonathan_kaz", "Progresivo, Electrónica, Experimental") == "Experimental"


def test_seed_puebla_genero_dominante(session):
    """El seed calcula `genero_dominante` para artistas con géneros."""
    from db.models import Artist

    artista = session.query(Artist).filter(Artist.generos.notlike("[PENDIENTE]")).first()
    assert artista is not None
    assert artista.genero_dominante in GENEROS_DOMINANTES
