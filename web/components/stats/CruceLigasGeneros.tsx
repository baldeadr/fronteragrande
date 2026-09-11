/** Matriz liga × género: cuántos proyectos hay de cada liga por género
 * dominante, con totales por liga y por género. Se renderiza del lado del
 * servidor (sin interacción). */

import { NIVEL_COLOR } from "@/components/stats/colores";

export default function CruceLigasGeneros({
  generos,
  matriz,
}: {
  generos: string[];
  matriz: Record<string, Record<string, number>>;
}) {
  const ligas = Object.keys(NIVEL_COLOR);
  const totalPorLiga = (liga: string) =>
    generos.reduce((acc, g) => acc + (matriz[liga]?.[g] || 0), 0);
  const totalPorGenero = (genero: string) =>
    ligas.reduce((acc, l) => acc + (matriz[l]?.[genero] || 0), 0);

  return (
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
          {ligas.map((liga) => (
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
                const total = totalPorLiga(liga);
                const pct = total ? Math.round((n / total) * 100) : 0;
                return (
                  <td
                    key={g}
                    className={`px-2 py-1.5 text-center tabular-nums ${
                      n > 0 ? "text-text" : "text-muted/40"
                    }`}
                  >
                    <div className="text-sm font-medium leading-tight">{n}</div>
                    {n > 0 && (
                      <div className="text-[11px] leading-tight text-muted">
                        {pct}%
                      </div>
                    )}
                  </td>
                );
              })}
              <td className="px-2 py-1.5 text-right font-bold tabular-nums">
                {totalPorLiga(liga)}
              </td>
            </tr>
          ))}
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
              {ligas.reduce(
                (acc, l) => acc + totalPorLiga(l),
                0,
              )}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}