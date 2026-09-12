"use client";

/** Dona de proyectos por género dominante (cada proyecto cuenta una vez).
 * Al seleccionar un género se listan los proyectos que lo integran, con
 * enlace a su perfil. */

import { useState } from "react";
import Link from "next/link";
import { GENERO_PALETA, OTRAS_COLOR } from "./colores";
import type { ArtistCard } from "@/lib/types";

const RADIO = 56;
const GROSOR = 26;

export default function DonaGeneros({
  artistas,
}: {
  artistas: ArtistCard[];
}) {
  const [sel, setSel] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);

  const conteo = new Map<string, number>();
  for (const a of artistas) {
    const k = a.genero_dominante || "Sin clasificar";
    conteo.set(k, (conteo.get(k) ?? 0) + 1);
  }
  const datos = Array.from(conteo.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([k, v], i) => ({ k, v, i }));
  const total = datos.reduce((acc, d) => acc + d.v, 0);
  const dim = RADIO * 2;
  const grosorInterior = RADIO - GROSOR / 2;
  const c = 2 * Math.PI * grosorInterior;

  const cortes = datos.reduce<
    { k: string; v: number; i: number; fraccion: number; inicio: number }[]
  >((acumulado, d) => {
    const anterior = acumulado.length
      ? acumulado[acumulado.length - 1].inicio
      : 0;
    const fraccion = d.v / total;
    acumulado.push({ ...d, fraccion, inicio: anterior + fraccion });
    return acumulado;
  }, []);

  const artistasDe = (genero: string) =>
    artistas
      .filter((a) => (a.genero_dominante || "Sin clasificar") === genero)
      .sort((a, b) => a.nombre.localeCompare(b.nombre));

  const colorDe = (k: string) => GENERO_PALETA[k] ?? OTRAS_COLOR;
  const seleccionado = sel !== null ? cortes.find((c) => c.k === sel) : undefined;

  return (
    <div>
      <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center">
        <svg viewBox={`0 0 ${dim} ${dim}`} className="h-36 w-36 shrink-0" role="img" aria-label="Distribución por género dominante">
          <g transform={`rotate(-90 ${RADIO} ${RADIO})`}>
            {cortes.map((corte) => {
              const activa = sel === corte.k;
              const atenuada =
                hover !== null && hover !== corte.k && !activa;
              return (
                <circle
                  key={corte.k}
                  cx={RADIO}
                  cy={RADIO}
                  r={grosorInterior}
                  fill="none"
                  stroke={colorDe(corte.k)}
                  strokeWidth={GROSOR}
                  strokeDasharray={`${corte.fraccion * c} ${c - corte.fraccion * c}`}
                  strokeDashoffset={-(corte.inicio - corte.fraccion) * c}
                  opacity={atenuada ? 0.35 : 1}
                  onMouseEnter={() => setHover(corte.k)}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => setSel(activa ? null : corte.k)}
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
          {datos.map((d) => (
            <button
              key={d.k}
              onMouseEnter={() => setHover(d.k)}
              onMouseLeave={() => setHover(null)}
              onClick={() => setSel(sel === d.k ? null : d.k)}
              className={`flex items-center gap-2 rounded-lg px-2 py-1 text-left transition-colors ${
                sel === d.k ? "bg-surface-2" : ""
              } ${hover === d.k ? "bg-surface-2/50" : ""}`}
            >
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: colorDe(d.k) }}
              />
              <span className="flex-1 text-muted">{d.k}</span>
              <span className="font-medium tabular-nums">{d.v}</span>
            </button>
          ))}
        </div>
      </div>

      <p className="mt-2 text-sm text-muted">
        {seleccionado ? (
          <span>
            <b>{seleccionado.k}</b> · {seleccionado.v} proyectos (
            {Math.round(seleccionado.fraccion * 100)}%)
          </span>
        ) : (
          <span className="text-xs">
            Toca un género para ver qué proyectos lo integran.
          </span>
        )}
      </p>

      {seleccionado && (
        <div className="mt-2 grid gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
          {artistasDe(seleccionado.k).map((a) => (
            <Link
              key={a.slug}
              href={`/artistas/${a.slug}`}
              className="flex items-center gap-2 rounded-lg border border-line bg-surface-2 px-3 py-1.5 text-sm transition-colors hover:bg-line/60"
            >
              <span className="truncate font-medium">{a.nombre}</span>
              <span className="ml-auto shrink-0 text-xs text-muted">
                {a.ciudad}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}