"use client";

/** Desglose por ciudad en barras apiladas con leyenda conmutable.
 *
 * Genérico para cualquier atributo (ligas, género dominante...): recibe las
 * filas por ciudad con un conteo por atributo y la definición estable de esos
 * atributos (clave, etiqueta, color). Replica la interacción de
 * `CiudadesApiladas`: leyenda que muestra/oculta capas y tooltip al pasar por
 * una barra.
 */

import { useState } from "react";
import { abreviaturaDeCiudad, ciudadBase } from "@/lib/ciudades";

export interface FilaDesglose {
  nombre: string;
  total: number;
  atributos: Record<string, number>;
}

export interface AtributoDesglose {
  clave: string;
  etiqueta: string;
  color: string;
}

export default function DesglosePorCiudad({
  filas,
  atributos,
  limite = 8,
}: {
  filas: FilaDesglose[];
  atributos: AtributoDesglose[];
  limite?: number;
}) {
  const [visibles, setVisibles] = useState<string[]>(
    atributos.map((a) => a.clave),
  );
  const [sel, setSel] = useState<number | null>(null);

  const filasVista = filas.slice(0, limite);
  const etiquetaPorClave = Object.fromEntries(
    atributos.map((a) => [a.clave, a.etiqueta]),
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-1">
        {atributos.map((a) => {
          const on = visibles.includes(a.clave);
          return (
            <button
              key={a.clave}
              onClick={() =>
                setVisibles((v) =>
                  on
                    ? v.filter((k) => k !== a.clave)
                    : [...v, a.clave],
                )
              }
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors ${
                on
                  ? "border-line bg-surface-2 text-text"
                  : "border-line bg-surface text-muted opacity-60"
              }`}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: a.color }}
              />
              {a.etiqueta}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-2">
        {filasVista.map((f, i) => {
          const activo = sel === i;
          const total = f.total > 0 ? f.total : 1;
          return (
            <div
              key={f.nombre}
              onMouseEnter={() => setSel(i)}
              onMouseLeave={() => setSel(null)}
              onClick={() => setSel(activo ? null : i)}
              className="flex cursor-pointer items-center gap-3 rounded-lg border border-transparent px-1 py-1 transition-colors hover:border-line"
            >
              <span className="w-28 shrink-0 truncate text-sm text-muted sm:w-36">
                {ciudadBase(f.nombre)}
                {abreviaturaDeCiudad(f.nombre)
                  ? ` ${abreviaturaDeCiudad(f.nombre)}`
                  : ""}
              </span>
              <div className="flex h-5 flex-1 overflow-hidden rounded bg-surface-2">
                {atributos.map((a) =>
                  visibles.includes(a.clave) && (f.atributos[a.clave] || 0) > 0 ? (
                    <div
                      key={a.clave}
                      style={{
                        width: `${((f.atributos[a.clave] || 0) / total) * 100}%`,
                        backgroundColor: a.color,
                      }}
                    />
                  ) : null,
                )}
              </div>
              <span className="w-8 shrink-0 text-right text-sm font-medium tabular-nums text-muted">
                {f.total}
              </span>
            </div>
          );
        })}
      </div>

      <p className="mt-2 min-h-5 text-sm text-muted">
        {sel !== null ? (
          <span>
            <b>{filasVista[sel].nombre}</b> · {filasVista[sel].total} proyectos:{" "}
            {atributos
              .map((a) => ({
                a,
                n: filasVista[sel].atributos[a.clave] || 0,
              }))
              .filter(({ n }) => n > 0)
              .map(({ a, n }, i) => (
                <span key={a.clave}>
                  {i > 0 && ", "}
                  {etiquetaPorClave[a.clave]}{" "}
                  <b className="tabular-nums">
                    {n}{" "}
                    <span className="text-muted">
                      (
                      {Math.round((n / filasVista[sel].total) * 100) || 0}
                      %)
                    </span>
                  </b>
                </span>
              ))}
          </span>
        ) : (
          <span className="text-xs">
            Toca la leyenda para ocultar una categoría o una barra para verla
            con sus cantidades y porcentajes.
          </span>
        )}
      </p>
    </div>
  );
}