#!/usr/bin/env python3
"""Genera los carruseles de redes sociales de Frontera Grande.

Uso:
    python scripts/generar_carruseles.py                     # todos, ambos formatos
    python scripts/generar_carruseles.py --carrusel artistas --formato reel

Cada carrusel vive en scripts/carruseles/<nombre>.py y su salida se escribe
en carrousel/<carpeta>/ (SVG + PNG vía Inkscape).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from carruseles import sistema
from carruseles import artistas, fans, presentacion

CARRUSELES = {
    presentacion.CARPETA: presentacion.SLIDES,
    artistas.CARPETA: artistas.SLIDES,
    fans.CARPETA: fans.SLIDES,
}
ALIAS = {"artistas": artistas.CARPETA}


def main():
    parser = argparse.ArgumentParser(description="Genera carruseles de RRSS")
    parser.add_argument("--carrusel", choices=[*CARRUSELES, *ALIAS, "todos"],
                        default="todos", help="qué carrusel generar")
    parser.add_argument("--formato", choices=[*sistema.FORMATOS, "ambos"],
                        default="ambos", help="formato de salida")
    args = parser.parse_args()

    formatos = sistema.FORMATOS if args.formato == "ambos" else {
        args.formato: sistema.FORMATOS[args.formato]}
    clave = ALIAS.get(args.carrusel, args.carrusel)
    objetivos = CARRUSELES if clave == "todos" else {clave: CARRUSELES[clave]}

    total = 0
    for carpeta, slides in objetivos.items():
        total += len(sistema.render(slides, carpeta, formatos))
    print(f"Total: {total} imágenes")


if __name__ == "__main__":
    main()
