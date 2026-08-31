"use client";

/** Dona de distribución porcentual por ciudad con tope y agrupación "Otras". */

import { useState } from "react";
import { CIUDAD_PALETA, OTRAS_COLOR } from "./colores";
import { abreviaturaDeCiudad, ciudadBase } from "@/lib/ciudades";

const RADIO = 56;
const GROSOR = 26;
const OTRAS = "__otras__";

function etiqueta(ciudad: string): string {
  if (ciudad === OTRAS) return "Otras";
  const base = ciudadBase(ciudad);
  const abrev = abreviaturaDeCiudad(ciudad);
  return abrev ? `${base} ${abrev}` : base;
}

export default function DonaCiudades({
  ciudades,
  limite = 8,
}: {
  ciudades: Record<string, number>;
  limite?: number;
}) {
  const [sel, setSel] = useState<number | null>(null);

  const ordenadas = Object.entries(ciudades).sort((a, b) => b[1] - a[1]);
  const visibles = ordenadas.slice(0, limite);
  const resto = ordenadas.slice(limite).reduce((acc, [, v]) => acc + v, 0);
  const datos =
    resto > 0 ? [...visibles, [OTRAS, resto] as [string, number]] : visibles;
  const total = datos.reduce((acc, [, v]) => acc + v, 0);
  const dim = RADIO * 2;
  const grosorInterior = RADIO - GROSOR / 2;
  const c = 2 * Math.PI * grosorInterior;

  const cortes = datos.reduce<
    { k: string; v: number; i: number; fraccion: number; inicio: number }[]
  >((acumulado, [k, v], i) => {
    const anterior = acumulado.length
      ? acumulado[acumulado.length - 1].inicio
      : 0;
    const fraccion = v / total;
    acumulado.push({ k, v, i, fraccion, inicio: anterior + fraccion });
    return acumulado;
  }, []);

  const colorDe = (i: number, k: string) =>
    k === OTRAS ? OTRAS_COLOR : CIUDAD_PALETA[i % CIUDAD_PALETA.length];

  return (
    <div>
      <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center">
        <svg
          viewBox={`0 0 ${dim} ${dim}`}
          className="h-36 w-36 shrink-0"
          role="img"
          aria-label="Distribución porcentual por ciudad"
        >
          <g transform={`rotate(-90 ${RADIO} ${RADIO})`}>
            {cortes.map((corte) => {
              const activa = sel === corte.i;
              return (
                <circle
                  key={corte.k}
                  cx={RADIO}
                  cy={RADIO}
                  r={grosorInterior}
                  fill="none"
                  stroke={colorDe(corte.i, corte.k)}
                  strokeWidth={GROSOR}
                  strokeDasharray={`${corte.fraccion * c} ${c - corte.fraccion * c}`}
                  strokeDashoffset={-(corte.inicio - corte.fraccion) * c}
                  opacity={sel === null || activa ? 1 : 0.3}
                  onMouseEnter={() => setSel(corte.i)}
                  onMouseLeave={() => setSel(null)}
                  onClick={() => setSel(activa ? null : corte.i)}
                  className="cursor-pointer"
                  style={{ transition: "opacity 120ms" }}
                />
              );
            })}
          </g>
          <text
            x={RADIO}
            y={RADIO - 4}
            textAnchor="middle"
            fontSize={20}
            fontWeight={700}
            fill="var(--text)"
          >
            {total}
          </text>
          <text
            x={RADIO}
            y={RADIO + 14}
            textAnchor="middle"
            fontSize={9}
            fill="var(--muted)"
          >
            proyectos
          </text>
        </svg>
        <div className="flex flex-col gap-1.5 text-sm">
          {datos.map(([k, v], i) => (
            <button
              key={k}
              onMouseEnter={() => setSel(i)}
              onMouseLeave={() => setSel(null)}
              onClick={() => setSel(sel === i ? null : i)}
              className={`flex items-center gap-2 rounded-lg px-2 py-1 text-left transition-colors ${
                sel === i ? "bg-surface-2" : ""
              }`}
            >
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: colorDe(i, k) }}
              />
              <span className="flex-1 text-muted">{etiqueta(k)}</span>
              <span className="font-medium tabular-nums">
                {v}
                <span className="ml-1 text-muted">
                  ({Math.round((v / total) * 100)}%)
                </span>
              </span>
            </button>
          ))}
        </div>
      </div>
      <p className="mt-2 min-h-5 text-sm text-muted">
        {sel !== null ? (
          <span>
            <b>{etiqueta(datos[sel][0])}</b> · {datos[sel][1]} proyectos (
            {Math.round((datos[sel][1] / total) * 100)}%)
          </span>
        ) : (
          <span className="text-xs">
            Pasa el cursor o toca una ciudad para ver su peso.
          </span>
        )}
      </p>
    </div>
  );
}