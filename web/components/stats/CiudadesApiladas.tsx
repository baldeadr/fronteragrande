"use client";

/** Ciudades apiladas por estado de actividad con leyenda conmutable. */

import { useState } from "react";
import type { CiudadActividad } from "@/lib/types";

const ESTADOS: { clave: "activo" | "en_duda" | "inactivo"; etiqueta: string }[] =
  [
    { clave: "activo", etiqueta: "Activos" },
    { clave: "en_duda", etiqueta: "En duda" },
    { clave: "inactivo", etiqueta: "Inactivos" },
  ];

const COLOR_ESTADO: Record<string, string> = {
  activo: "var(--activo)",
  en_duda: "var(--en-duda)",
  inactivo: "var(--inactivo)",
};

export default function CiudadesApiladas({
  ciudades,
  limite = 8,
}: {
  ciudades: CiudadActividad[];
  limite?: number;
}) {
  const [visibles, setVisibles] = useState<string[]>([
    "activo",
    "en_duda",
    "inactivo",
  ]);
  const [sel, setSel] = useState<number | null>(null);

  const filas = ciudades.slice(0, limite);
  const max = Math.max(...filas.map((c) => c.total), 1);

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-1">
        {ESTADOS.map((e) => {
          const on = visibles.includes(e.clave);
          return (
            <button
              key={e.clave}
              onClick={() =>
                setVisibles((v) =>
                  on
                    ? v.filter((k) => k !== e.clave)
                    : [...v, e.clave],
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
                style={{ backgroundColor: COLOR_ESTADO[e.clave] }}
              />
              {e.etiqueta}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-2">
        {filas.map((c, i) => {
          const activo = sel === i;
          const totalVisible = ESTADOS.reduce(
            (acc, e) =>
              visibles.includes(e.clave) ? acc + c[e.clave] : acc,
            0,
          );
          return (
            <div
              key={c.nombre}
              onMouseEnter={() => setSel(i)}
              onMouseLeave={() => setSel(null)}
              onClick={() => setSel(activo ? null : i)}
              className="flex cursor-pointer items-center gap-3 rounded-lg border border-transparent px-1 py-1 transition-colors hover:border-line"
            >
              <span className="w-28 shrink-0 truncate text-sm text-muted sm:w-36">
                {c.nombre}
              </span>
              <div className="flex h-5 flex-1 overflow-hidden rounded bg-surface-2">
                {ESTADOS.map((e) =>
                  visibles.includes(e.clave) && c[e.clave] > 0 ? (
                    <div
                      key={e.clave}
                      style={{
                        width: `${(c[e.clave] / max) * 100}%`,
                        backgroundColor: COLOR_ESTADO[e.clave],
                      }}
                    />
                  ) : null,
                )}
              </div>
              <span className="w-8 shrink-0 text-right text-sm font-medium tabular-nums text-muted">
                {totalVisible}
              </span>
            </div>
          );
        })}
      </div>

      <p className="mt-2 min-h-5 text-sm text-muted">
        {sel !== null ? (
          <span>
            <b>{filas[sel].nombre}</b> · {filas[sel].total} proyectos:{" "}
            {ESTADOS.map((e, i) => (
              <span key={e.clave}>
                {i > 0 && ", "}
                {filas[sel][e.clave]} {e.etiqueta.toLowerCase()}
              </span>
            ))}
          </span>
        ) : (
          <span className="text-xs">
            Toca la leyenda para ocultar un estado o una barra para verla.
          </span>
        )}
      </p>
    </div>
  );
}