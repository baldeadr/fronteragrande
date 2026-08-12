"use client";

/** Barras horizontales del estado de registro (procedencia de los perfiles). */

import { useState } from "react";

const ETIQUETAS: Record<string, string> = {
  "investigado (web)": "Investigado (web)",
  "confirmado (artista)": "Confirmado por el artista",
  "registrado (formulario, sin conectar)": "Registrado por formulario",
  "agregado (formulario)": "Registrado por formulario",
  "conviviente (propio)": "Conviviente (propio)",
  "confirmado parcial (redes por el artista)": "Confirmado parcial",
  "sin confirmar": "Sin confirmar",
};

export default function EstadoRegistroBarras({
  estados,
}: {
  estados: Record<string, number>;
}) {
  const [sel, setSel] = useState<number | null>(null);

  const datos = Object.entries(estados)
    .map(([k, v]) => ({
      clave: k,
      etiqueta: ETIQUETAS[k] ?? k,
      valor: v,
    }))
    .sort((a, b) => b.valor - a.valor);

  const max = Math.max(...datos.map((d) => d.valor), 1);

  return (
    <div className="flex flex-col gap-2">
      {datos.map((d, i) => {
        const activo = sel === i;
        return (
          <div
            key={d.clave}
            onMouseEnter={() => setSel(i)}
            onMouseLeave={() => setSel(null)}
            onClick={() => setSel(activo ? null : i)}
            className="flex cursor-pointer items-center gap-3 rounded-lg border border-transparent px-1 py-1 transition-colors hover:border-line"
          >
            <span className="w-40 shrink-0 truncate text-sm text-muted sm:w-52">
              {d.etiqueta}
            </span>
            <div className="flex h-5 flex-1 overflow-hidden rounded bg-surface-2">
              <div
                style={{
                  width: `${(d.valor / max) * 100}%`,
                  backgroundColor:
                    d.clave === "confirmado (artista)"
                      ? "var(--accent)"
                      : d.clave === "conviviente (propio)"
                        ? "var(--activo)"
                        : "var(--muted)",
                }}
              />
            </div>
            <span className="w-8 shrink-0 text-right text-sm font-medium tabular-nums text-muted">
              {d.valor}
            </span>
          </div>
        );
      })}
    </div>
  );
}
