"use client";

/** Matriz liga × género: cuántos proyectos hay de cada liga por género
 * dominante, con totales por liga y por género. Permite rebanar por ciudad
 * (drill-down): por defecto muestra toda la escena y, si se elige una plaza,
 * la matriz es la de esa ciudad.
 *
 * El porcentaje de cada celda es dentro de su liga y se muestra siempre que
 * la celda tenga proyectos. La columna y la fila de Total muestran la
 * participación de cada liga / género sobre el total de la vista (escena
 * completa o la ciudad elegida). */

import { useState } from "react";
import { NIVEL_COLOR } from "@/components/stats/colores";
import { IconoLiga } from "@/components/IconoLiga";

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
  const granTotal = ligas.reduce((acc, l) => acc + totalPorLiga(l), 0);
  const pctDeEscena = (n: number) =>
    granTotal > 0 ? Math.round((n / granTotal) * 100) : 0;

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
              return (
                <tr key={liga} className="border-t border-line">
                  <td className="sticky left-0 z-10 whitespace-nowrap bg-surface py-1.5 pr-3 font-medium">
                    <span className="inline-flex items-center gap-2">
                      <span style={{ color: NIVEL_COLOR[liga] }}>
                        <IconoLiga nivel={liga} className="h-3.5 w-3.5" />
                      </span>
                      {liga}
                    </span>
                  </td>
                  {generos.map((g) => {
                    const n = matriz[liga]?.[g] || 0;
                    const pct = total
                      ? Math.round((n / total) * 100)
                      : 0;
                    const mostrarPct = n > 0;
                    // Heatmap: intensidad del color de la liga según el % dentro
                    // de esa liga (0 = celda vacía). El % se muestra siempre que
                    // la celda tenga proyectos.
                    const alfa = n > 0
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
                        {mostrarPct && (
                          <div className="text-[11px] leading-tight text-muted">
                            {pct}%
                          </div>
                        )}
                      </td>
                    );
                  })}
                  <td className="px-2 py-1.5 text-right font-bold tabular-nums">
                    {total}
                    {total > 0 && (
                      <div className="text-[11px] font-normal leading-tight text-muted">
                        {pctDeEscena(total)}%
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
                    {n > 0 && (
                      <div className="text-[10px] font-normal leading-tight text-muted/70">
                        {pctDeEscena(n)}%
                      </div>
                    )}
                  </td>
                );
              })}
              <td className="px-2 py-1.5 text-right text-xs font-bold tabular-nums text-muted">
                {granTotal}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}