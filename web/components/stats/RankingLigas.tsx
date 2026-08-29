"use client";

/** Ranking de Ligas: Ligas Mayores, En Ascenso y Leyenda de la Frontera en una
 *  misma gráfica aparte, separada del ranking de la escena local. */

import Link from "next/link";
import type { ArtistCard } from "@/lib/types";
import InsigniaNivel from "@/components/InsigniaNivel";

const GRUPO_COLOR = { audiencia: "var(--accent)", consumo: "#f5a623" };

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

export default function RankingLigas({ artistas }: { artistas: ArtistCard[] }) {
  const catalogados = artistas
    .filter((a) => a.catalogado && a.ranking.indice !== null && a.ranking.indice > 0)
    .sort(
      (a, b) =>
        (b.ranking.indice as number) - (a.ranking.indice as number),
    );
  const max = Math.max(...catalogados.map((a) => a.ranking.indice as number), 1);

  if (catalogados.length === 0) {
    return (
      <p className="text-sm text-muted">
        Aún no hay artistas catalogados en las Ligas.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {catalogados.map((a) => {
        const partes = desglose(a);
        return (
          <div key={a.slug} className="rounded-lg border border-line px-2 py-1.5">
            <div className="flex items-center gap-3">
              <span className="w-8 shrink-0 text-sm font-bold text-accent">
                #{a.ranking.rank}
              </span>
              <Link
                href={`/artistas/${a.slug}`}
                className="w-28 shrink-0 truncate text-sm text-muted transition-colors hover:text-accent sm:w-40"
                title={a.nombre}
              >
                {a.nombre}
              </Link>
              <InsigniaNivel nivel={a.nivel} size="sm" />
              <div className="flex h-5 flex-1 items-stretch overflow-hidden rounded bg-surface-2">
                {partes.length > 0 ? (
                  partes.map((p) => (
                    <div
                      key={p.clave}
                      style={{
                        width: `${
                          (p.share * ((a.ranking.indice as number) / max)) * 100
                        }%`,
                        minWidth: p.share > 0.9 ? undefined : 2,
                        backgroundColor:
                          GRUPO_COLOR[p.clave as keyof typeof GRUPO_COLOR],
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
  );
}
