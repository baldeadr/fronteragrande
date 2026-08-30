"use client";

/** Ranking de alcance con filtros por grupo: la Escena (base) y las Ligas.
 *  Re-ranquea 1..N dentro del grupo seleccionado; la posición oficial de la
 *  API no cambia (esa se ve en el perfil del artista). */

import { useState } from "react";
import Link from "next/link";
import type { ArtistCard } from "@/lib/types";
import InsigniaNivel from "@/components/InsigniaNivel";

const GRUPO_COLOR = { audiencia: "var(--accent)", consumo: "#f5a623" };

const COLOR_NIVEL: Record<string, string> = {
  "Ligas Mayores": "#f5b301",
  "En Ascenso": "#2fb8a6",
  "Leyenda de la Frontera": "#8a63d2",
};

type ClaveGrupo = "escena" | "ligas_mayores" | "en_ascenso" | "leyenda" | "ligas";

const GRUPOS: {
  clave: ClaveGrupo;
  etiqueta: string;
  color: string;
  seleccionar: (a: ArtistCard) => boolean;
}[] = [
  {
    clave: "escena",
    etiqueta: "Escena",
    color: "var(--accent)",
    seleccionar: (a) => !a.catalogado,
  },
  {
    clave: "ligas_mayores",
    etiqueta: "Ligas Mayores",
    color: COLOR_NIVEL["Ligas Mayores"],
    seleccionar: (a) => a.nivel === "Ligas Mayores",
  },
  {
    clave: "en_ascenso",
    etiqueta: "En Ascenso",
    color: COLOR_NIVEL["En Ascenso"],
    seleccionar: (a) => a.nivel === "En Ascenso",
  },
  {
    clave: "leyenda",
    etiqueta: "Leyenda",
    color: COLOR_NIVEL["Leyenda de la Frontera"],
    seleccionar: (a) => a.nivel === "Leyenda de la Frontera",
  },
  {
    clave: "ligas",
    etiqueta: "Ligas",
    color: "var(--text)",
    seleccionar: (a) => a.catalogado,
  },
];

function desglose(a: ArtistCard) {
  const audiencia = a.ranking.audiencia ?? 0;
  const consumo = a.ranking.consumo ?? 0;
  const total = audiencia + consumo;
  if (!total) return [];
  return [
    { clave: "audiencia", share: audiencia / total },
    { clave: "consumo", share: consumo / total },
  ].filter((p) => p.share > 0);
}

const LIMITES: { valor: number | null; texto: string }[] = [
  { valor: 5, texto: "Top 5" },
  { valor: 10, texto: "Top 10" },
  { valor: 20, texto: "Top 20" },
  { valor: null, texto: "Todos" },
];

export default function RankingFiltrable({
  artistas,
}: {
  artistas: ArtistCard[];
}) {
  const [grupo, setGrupo] = useState<ClaveGrupo>("escena");
  const [limite, setLimite] = useState<number | null>(10);
  const [sel, setSel] = useState<string | null>(null);

  const grupoActivo = GRUPOS.find((g) => g.clave === grupo)!;
  const conIndice = artistas
    .filter(grupoActivo.seleccionar)
    .filter((a) => a.ranking.indice !== null && a.ranking.indice > 0)
    .sort(
      (a, b) =>
        (b.ranking.indice as number) - (a.ranking.indice as number),
    );
  const visibles = limite === null ? conIndice : conIndice.slice(0, limite);
  const max = Math.max(...visibles.map((a) => a.ranking.indice as number), 1);
  const foco = conIndice.find((a) => a.slug === sel) ?? null;
  const esLiga = grupo !== "escena";

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-1">
        {GRUPOS.map((g) => {
          const conteo = artistas.filter(g.seleccionar).length;
          const activo = grupo === g.clave;
          return (
            <button
              key={g.clave}
              onClick={() => setGrupo(g.clave)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors ${
                activo
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-line bg-surface-2 text-muted hover:text-text"
              }`}
            >
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ backgroundColor: g.color }}
              />
              {g.etiqueta}
              <span
                className={`tabular-nums ${activo ? "text-accent" : "text-muted"}`}
              >
                {conteo}
              </span>
            </button>
          );
        })}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1">
        <div className="flex gap-1">
          {LIMITES.map((l) => (
            <button
              key={l.texto}
              onClick={() => setLimite(l.valor)}
              className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
                limite === l.valor
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-line bg-surface-2 text-muted hover:text-text"
              }`}
            >
              {l.texto}
            </button>
          ))}
        </div>
        <span className="ml-auto flex gap-x-3 gap-y-1 text-xs text-muted">
          {["audiencia", "consumo"].map((clave) => (
            <span
              key={clave}
              className="inline-flex items-center gap-1.5"
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor:
                    GRUPO_COLOR[clave as keyof typeof GRUPO_COLOR],
                }}
              />
              {clave === "audiencia" ? "Audiencia" : "Consumo"}
            </span>
          ))}
        </span>
      </div>

      {conIndice.length === 0 ? (
        <p className="text-sm text-muted">
          Aún no hay proyectos con índice calculado en este grupo.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {visibles.map((a, i) => {
            const partes = desglose(a);
            const activo = sel === a.slug;
            return (
              <div
                key={a.slug}
                onMouseEnter={() => setSel(a.slug)}
                onMouseLeave={() => setSel(null)}
                onClick={() => setSel(activo ? null : a.slug)}
                className="cursor-pointer rounded-lg border border-transparent px-1 py-1 transition-colors hover:border-line"
              >
                <div className="flex items-center gap-3">
                  <span className="w-8 shrink-0 text-sm font-bold text-accent">
                    #{i + 1}
                  </span>
                  <Link
                    href={`/artistas/${a.slug}`}
                    onClick={(e) => e.stopPropagation()}
                    className="w-28 shrink-0 truncate text-sm text-muted transition-colors hover:text-accent sm:w-40"
                    title={a.nombre}
                  >
                    {a.nombre}
                  </Link>
                  {esLiga && <InsigniaNivel nivel={a.nivel} size="sm" />}
                  <div className="flex h-5 flex-1 items-stretch overflow-hidden rounded bg-surface-2">
                    {partes.length > 0 ? (
                      partes.map((p) => (
                        <div
                          key={p.clave}
                          style={{
                            width: `${
                              (p.share * ((a.ranking.indice as number) / max)) *
                              100
                            }%`,
                            minWidth: p.share > 0.9 ? undefined : 2,
                            backgroundColor:
                              GRUPO_COLOR[
                                p.clave as keyof typeof GRUPO_COLOR
                              ],
                          }}
                          title={p.clave.toUpperCase()}
                        />
                      ))
                    ) : (
                      <div
                        className="h-full rounded bg-accent"
                        style={{
                          width: `${((a.ranking.indice as number) / max) * 100}%`,
                        }}
                      />
                    )}
                  </div>
                  <span className="w-9 shrink-0 text-right text-sm font-medium tabular-nums text-muted">
                    {a.ranking.indice}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="mt-2 min-h-5 text-sm text-muted">
        {foco ? (
          <span>
            <b>{foco.nombre}</b> · índice {foco.ranking.indice} de{" "}
            {foco.ranking.total}:{" "}
            {desglose(foco)
              .map((p) => `${p.clave.toUpperCase()} ${Math.round(p.share * 100)}%`)
              .join(", ")}
          </span>
        ) : (
          <span className="text-xs">
            Pasa el cursor o toca una fila para ver la proporción de audiencia
            y consumo · posición dentro del grupo mostrado.
          </span>
        )}
      </p>
    </div>
  );
}