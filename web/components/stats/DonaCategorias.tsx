"use client";

/** Dona de distribución por categoría con contexto al pasar/tocar. */

import { useState } from "react";
import { CATEGORIA_COLOR } from "./colores";

const RADIO = 56;
const GROSOR = 26;

export default function DonaCategorias({
  segmentos,
}: {
  segmentos: Record<string, number>;
}) {
  const [sel, setSel] = useState<number | null>(null);

  const datos = Object.entries(segmentos).sort((a, b) => b[1] - a[1]);
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

  return (
    <div>
      <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center">
        <svg viewBox={`0 0 ${dim} ${dim}`} className="h-36 w-36 shrink-0" role="img" aria-label="Distribución por categoría">
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
                  stroke={CATEGORIA_COLOR[corte.k] ?? "var(--accent)"}
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
                style={{ backgroundColor: CATEGORIA_COLOR[k] ?? "var(--accent)" }}
              />
              <span className="flex-1 text-muted">{k}</span>
              <span className="font-medium tabular-nums">{v}</span>
            </button>
          ))}
        </div>
      </div>
      <p className="mt-2 min-h-5 text-sm text-muted">
        {sel !== null ? (
          <span>
            <b>{datos[sel][0]}</b> · {datos[sel][1]} proyectos (
            {Math.round((datos[sel][1] / total) * 100)}%)
          </span>
        ) : (
          <span className="text-xs">
            Pasa el cursor o toca una categoría para ver su peso.
          </span>
        )}
      </p>
    </div>
  );
}
