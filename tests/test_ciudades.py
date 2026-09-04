"""Normalización del lado de frontera (TM/TX) de las ciudades.

Protege `lib.helpers.ciudad_base` y `lib.helpers.normalizar_ciudad`: toda ciudad
de la región cerrada (Tamaulipas + Valle del Río Grande) debe terminar en TM o
TX con una sola forma canónica, y los valores desconocidos no se inventan.
"""

from lib.helpers import ciudad_base, normalizar_ciudad


def test_ciudad_base_quita_estado_y_sufijo():
    assert ciudad_base("Roma, Texas") == "Roma"
    assert ciudad_base("Brownsville, Texas") == "Brownsville"
    assert ciudad_base("Reynosa TM") == "Reynosa"
    assert ciudad_base("Hidalgo TX") == "Hidalgo"
    assert ciudad_base("Reynosa") == "Reynosa"
    assert ciudad_base("") == ""
    assert ciudad_base(None) == ""


def test_normalizar_tamaulipas():
    assert normalizar_ciudad("Reynosa") == "Reynosa TM"
    assert normalizar_ciudad("Reynosa TM") == "Reynosa TM"
    assert normalizar_ciudad("Matamoros") == "Matamoros TM"
    assert normalizar_ciudad("Río Bravo TM") == "Río Bravo TM"
    assert normalizar_ciudad("Río Bravo") == "Río Bravo TM"
    assert normalizar_ciudad("Díaz Ordaz") == "Díaz Ordaz TM"
    assert normalizar_ciudad("Camargo TM") == "Camargo TM"
    assert normalizar_ciudad("Cd. Camargo") == "Cd. Camargo TM"


def test_normalizar_valle_rio_grande():
    assert normalizar_ciudad("McAllen") == "McAllen TX"
    assert normalizar_ciudad("Edinburg, Texas") == "Edinburg TX"
    assert normalizar_ciudad("Laredo") == "Laredo TX"
    assert normalizar_ciudad("Roma, Texas") == "Roma TX"
    assert normalizar_ciudad("Hidalgo TX") == "Hidalgo TX"
    assert normalizar_ciudad("South Padre Island, Texas") == "South Padre Island TX"
    assert normalizar_ciudad("Brownsville, Texas") == "Brownsville TX"


def test_normalizar_no_inventa_lado():
    assert normalizar_ciudad("") == ""
    assert normalizar_ciudad(None) == ""
    assert normalizar_ciudad("[PENDIENTE]") == "[PENDIENTE]"
    assert normalizar_ciudad("Ciudad Victoria") == "Ciudad Victoria"