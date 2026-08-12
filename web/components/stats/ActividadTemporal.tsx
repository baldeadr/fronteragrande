"use client";

/** Barras verticales de una serie mensual (conteo por mes) con contexto. */

import { useState } from "react";
import { mesCorto, etiquetaMes } from "@/lib/formato";
import type { SerieMes } from "@/lib/types";

const ANCHO = 320;
const ALTO = 132;
const MARGEN_BASE = 20;
const TOP = 8;

export default function ActividadTemporal({
  serie,
  color = "var(--accent)",
  rotulo = "publicaciones",
}: {
  serie: SerieMes[];
  color?: string;
  rotulo?: string;
}) {
  const [sel, setSel] = useState<number | null>(null);

  if (!serie.length) {
    return <p className="text-sm text-muted">Sin datos para graficar.</p>;
  }

  const max = Math.max(...serie.map((s) => s.conteo), 1);
  const n = serie.length;
  const paso = ANCHO / n;
  const barra = Math.max(8, paso * 0.55);
  const altoUtil = ALTO - MARGEN_BASE - TOP;

  return (
    <div>
      <svg
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        className="w-full"
        role="img"
        aria-label={`${rotulo} por mes`}
      >
        {serie.map((s, i) => {
          const h = (s.conteo / max) * altoUtil;
          const x = i * paso + (paso - barra) / 2;
          const y = ALTO - MARGEN_BASE - h;
          const activa = sel === i;
          return (
            <g
              key={s.mes}
              onMouseEnter={() => setSel(i)}
              onMouseLeave={() => setSel(null)}
              onClick={() => setSel(activa ? null : i)}
              className="cursor-pointer"
            >
              <rect
                x={x}
                y={TOP}
                width={barra}
                height={altoUtil}
                fill="transparent"
              />
              <rect
                x={x}
                y={y}
                width={barra}
                height={h}
                rx={3}
                fill={color}
                opacity={h === 0 ? 0.18 : activa ? 1 : 0.55}
                style={{ transition: "opacity 120ms" }}
              />
              <text
                x={x + barra / 2}
                y={ALTO - 5}
                textAnchor="middle"
                fontSize={8}
                fill="var(--muted)"
              >
                {mesCorto(s.mes)}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="mt-1 min-h-5 text-sm text-muted">
        {sel !== null ? (
          <span>
            <b>{etiquetaMes(serie[sel].mes)}</b> · {serie[sel].conteo}{" "}
            {rotulo}
          </span>
        ) : (
          <span className="text-xs">
            Pasa el cursor o toca una barra para ver el mes.
          </span>
        )}
      </p>
    </div>
  );
}