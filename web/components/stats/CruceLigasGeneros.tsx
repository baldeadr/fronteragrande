"use client";

/** Matriz liga × género: cuántos proyectos hay de cada liga por género
 * dominante, con totales por liga y por género. Permite rebanar por ciudad
 * (drill-down): por defecto muestra toda la escena y, si se elige una plaza,
 * la matriz es la de esa ciudad.
 *
 * El porcentaje de cada celda es dentro de su liga; solo se muestra cuando la
 * liga tiene suficientes proyectos para que no sea ruido (1 proyecto = 100%). */

import { useState } from "react";
import { NIVEL_COLOR } from "@/components/stats/colores";

const MIN_PROYECTOS_PARA_PCT = 5;

type Matriz = Record<string, Record<string, number>>;

function hexToRgba(hex: string, alfa: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alfa})`;
}

export default function CruceLigasGeneros({
  generos,
  ciudades,
  matrizGlobal,
  matrizPorCiudad,
}: {
  generos: string[];
  ciudades: string[];
  matrizGlobal: Matriz;
  matrizPorCiudad: Record<string, Matriz>;
}) {
  const [ciudadSel, setCiudadSel] = useState("");
  const matriz = ciudadSel ? matrizPorCiudad[ciudadSel] ?? {} : matrizGlobal;
  const ligas = Object.keys(NIVEL_COLOR);
  const totalPorLiga = (liga: string) =>
    generos.reduce((acc, g) => acc + (matriz[liga]?.[g] || 0), 0);
  const totalPorGenero = (genero: string) =>
    ligas.reduce((acc, l) => acc + (matriz[l]?.[genero] || 0), 0);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <label
          htmlFor="cruce-ciudad"
          className="text-xs font-semibold text-muted"
        >
          Ciudad
        </label>
        <select
          id="cruce-ciudad"
          value={ciudadSel}
          onChange={(e) => setCiudadSel(e.target.value)}
          className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-text outline-none focus:border-accent"
        >
          <option value="">Toda la escena</option>
          {ciudades.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-surface text-left text-xs font-semibold text-muted">
                Liga
              </th>
              {generos.map((g) => (
                <th
                  key={g}
                  className="whitespace-nowrap px-2 py-1 text-xs font-semibold text-muted"
                >
                  {g}
                </th>
              ))}
              <th className="px-2 py-1 text-right text-xs font-semibold text-muted">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            {ligas.map((liga) => {
              const total = totalPorLiga(liga);
              const mostrarPct = total >= MIN_PROYECTOS_PARA_PCT;
              return (
                <tr key={liga} className="border-t border-line">
                  <td className="sticky left-0 z-10 whitespace-nowrap bg-surface py-1.5 pr-3 font-medium">
                    <span className="inline-flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: NIVEL_COLOR[liga] }}
                      />
                      {liga}
                    </span>
                  </td>
                  {generos.map((g) => {
                    const n = matriz[liga]?.[g] || 0;
                    const pct = mostrarPct && total
                      ? Math.round((n / total) * 100)
                      : 0;
                    // Heatmap: intensidad del color de la liga según el % dentro
                    // de esa liga (0 = celda vacía).
                    const alfa = mostrarPct && n > 0
                      ? 0.1 + 0.55 * (pct / 100)
                      : 0;
                    return (
                      <td
                        key={g}
                        className={`px-2 py-1.5 text-center tabular-nums ${
                          n > 0 ? "text-text" : "text-muted/40"
                        }`}
                        style={{
                          backgroundColor:
                            alfa > 0
                              ? hexToRgba(NIVEL_COLOR[liga], alfa)
                              : undefined,
                        }}
                      >
                        <div className="text-sm font-medium leading-tight">
                          {n}
                        </div>
                        {mostrarPct && n > 0 && (
                          <div className="text-[11px] leading-tight text-muted">
                            {pct}%
                          </div>
                        )}
                      </td>
                    );
                  })}
                  <td className="px-2 py-1.5 text-right font-bold tabular-nums">
                    {total}
                    {mostrarPct && (
                      <div className="text-[11px] font-normal leading-tight text-muted">
                        100%
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="border-t border-line">
              <td className="sticky left-0 z-10 whitespace-nowrap bg-surface py-1.5 pr-3 text-xs font-semibold text-muted">
                Total
              </td>
              {generos.map((g) => {
                const n = totalPorGenero(g);
                return (
                  <td
                    key={g}
                    className={`px-2 py-1.5 text-center text-xs font-semibold tabular-nums ${
                      n > 0 ? "text-muted" : "text-muted/40"
                    }`}
                  >
                    {n}
                  </td>
                );
              })}
              <td className="px-2 py-1.5 text-right text-xs font-bold tabular-nums text-muted">
                {ligas.reduce((acc, l) => acc + totalPorLiga(l), 0)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}