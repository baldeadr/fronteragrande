"use client";

/** Ecosistema de redes: audiencia acumulada por plataforma + cobertura. */

import { useState } from "react";
import IconoRed from "@/components/IconoRed";
import { infoPlataforma } from "@/components/Plataformas";
import { numeroGrande } from "@/lib/formato";
import { PLATAFORMA_COLOR } from "./colores";

const FILAS: { clave: string; clase: "seguidores" | "reproducciones" }[] = [
  { clave: "ig", clase: "seguidores" },
  { clave: "fb", clase: "seguidores" },
  { clave: "yt", clase: "seguidores" },
  { clave: "tt", clase: "seguidores" },
  { clave: "spotify", clase: "seguidores" },
  { clave: "bandcamp", clase: "reproducciones" },
  { clave: "soundcloud", clase: "reproducciones" },
  { clave: "beatport", clase: "seguidores" },
  { clave: "mixcloud", clase: "seguidores" },
];

export default function EcosistemaRedes({
  seguidores,
  reproducciones,
  cobertura,
}: {
  seguidores: Record<string, number>;
  reproducciones: Record<string, number>;
  cobertura: Record<string, number>;
}) {
  const [sel, setSel] = useState<string | null>(null);

  const conValor = FILAS.filter((f) => (seguidores[f.clave] ?? reproducciones[f.clave] ?? 0) > 0);
  const max = Math.max(
    ...conValor.map((f) => Math.log10((seguidores[f.clave] ?? reproducciones[f.clave] ?? 0) + 1)),
    1,
  );

  return (
    <div>
      <div className="flex flex-col gap-2">
        {FILAS.map((f) => {
          const valor = seguidores[f.clave] ?? reproducciones[f.clave] ?? 0;
          const color = PLATAFORMA_COLOR[f.clave] ?? "var(--accent)";
          const cov = cobertura[f.clave] ?? 0;
          const activo = sel === f.clave;
          const nombre = infoPlataforma(f.clave).nombre;
          return (
            <div
              key={f.clave}
              onMouseEnter={() => setSel(f.clave)}
              onMouseLeave={() => setSel(null)}
              onClick={() => setSel(activo ? null : f.clave)}
              className="flex cursor-pointer items-center gap-3 rounded-lg border border-transparent px-1 py-1 transition-colors hover:border-line"
            >
              <IconoRed
                src={infoPlataforma(f.clave).icono}
                alt={nombre}
                size={18}
              />
              <span className="w-24 shrink-0 truncate text-sm text-muted sm:w-32">
                {nombre}
              </span>
              <div className="h-4 flex-1 overflow-hidden rounded bg-surface-2">
                {valor > 0 && (
                  <div
                    className="h-full rounded"
                    style={{
                      width: `${(Math.log10(valor + 1) / max) * 100}%`,
                      backgroundColor: color,
                      opacity: activo ? 1 : 0.7,
                    }}
                  />
                )}
              </div>
              <span
                className={`w-16 shrink-0 text-right text-sm font-medium tabular-nums ${valor > 0 ? "text-text" : "text-muted"}`}
              >
                {valor > 0 ? numeroGrande(valor) : "—"}
              </span>
              <span
                className="w-12 shrink-0 rounded-full border border-line px-1.5 py-0.5 text-center text-xs tabular-nums text-muted"
                title={`${cov}% de los proyectos con métrica`}
              >
                {cov}%
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-2 min-h-5 text-sm text-muted">
        {sel ? (
          <span>
            <b>{infoPlataforma(sel).nombre}</b> ·{" "}
            {(seguidores[sel] ?? reproducciones[sel] ?? 0) > 0 ? (
              <>
                {numeroGrande(seguidores[sel] ?? reproducciones[sel] ?? 0)}{" "}
                {seguidores[sel] ? "seguidores" : "reproducciones"} en total
              </>
            ) : (
              "sin métrica registrada"
            )}{" "}
            · con dato el {cobertura[sel] ?? 0}% de los proyectos
          </span>
        ) : (
          <span className="text-xs">
            Audiencia acumulada de las redes. El porcentaje es cobertura: cuántos
            proyectos tienen la métrica en la base.
          </span>
        )}
      </p>
    </div>
  );
}