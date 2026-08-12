"use client";

/** Dona de perfiles verificados vs no verificados con contexto al tocar. */

import { useState } from "react";
import IconoVerificado from "../IconoVerificado";

const RADIO = 56;
const GROSOR = 26;

export default function DonaVerificados({
  verificados,
  total,
}: {
  verificados: number;
  total: number;
}) {
  const [sel, setSel] = useState<"si" | "no" | null>(null);

  const noVerificados = Math.max(0, total - verificados);
  const dim = RADIO * 2;
  const c = 2 * Math.PI * RADIO;

  const cortes = [
    {
      k: "si",
      valor: verificados,
      fraccion: total ? verificados / total : 0,
      color: "var(--accent)",
      etiqueta: "Verificados",
    },
    {
      k: "no",
      valor: noVerificados,
      fraccion: total ? noVerificados / total : 1,
      color: "var(--surface-2)",
      etiqueta: "Sin verificar",
    },
  ];

  let acumulado = 0;
  const segmentos = cortes.map((corte) => {
    const inicio = acumulado;
    acumulado += corte.fraccion;
    return { ...corte, inicio, fin: acumulado };
  });

  return (
    <div>
      <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center">
        <div className="relative shrink-0">
          <svg
            viewBox={`0 0 ${dim} ${dim}`}
            className="h-36 w-36"
            role="img"
            aria-label="Perfiles verificados vs no verificados"
          >
            <g transform={`rotate(-90 ${RADIO} ${RADIO})`}>
              {segmentos.map((seg) =>
                seg.fraccion > 0 ? (
                  <circle
                    key={seg.k}
                    cx={RADIO}
                    cy={RADIO}
                    r={RADIO - GROSOR / 2}
                    fill="transparent"
                    stroke={seg.color}
                    strokeWidth={GROSOR}
                    strokeDasharray={`${seg.fraccion * c} ${c}`}
                    strokeDashoffset={-seg.inicio * c}
                    opacity={
                      sel === null || sel === seg.k
                        ? 1
                        : 0.35
                    }
                    style={{ transition: "opacity 120ms" }}
                    className="cursor-pointer"
                    onMouseEnter={() => setSel(seg.k as "si" | "no")}
                    onMouseLeave={() => setSel(null)}
                    onClick={() => setSel(sel === seg.k ? null : (seg.k as "si" | "no"))}
                  />
                ) : null,
              )}
            </g>
          </svg>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <IconoVerificado className="h-6 w-6 text-accent" />
            <p className="mt-1 text-2xl font-bold tabular-nums">{verificados}</p>
          </div>
        </div>

        <ul className="flex w-full flex-col gap-1.5 sm:w-auto">
          {segmentos.map((seg) => (
            <li key={seg.k}>
              <button
                type="button"
                onClick={() => setSel(sel === seg.k ? null : (seg.k as "si" | "no"))}
                className={`flex w-full items-center justify-between gap-6 rounded-lg px-2 py-1 text-sm transition-colors ${
                  sel === seg.k ? "bg-surface-2" : ""
                }`}
              >
                <span className="flex items-center gap-2 text-muted">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: seg.color }}
                  />
                  {seg.etiqueta}
                </span>
                <span className="tabular-nums text-text">
                  {seg.valor}
                  <span className="ml-1 text-muted">
                    ({total ? Math.round(seg.fraccion * 100) : 0}%)
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
