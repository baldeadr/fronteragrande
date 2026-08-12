"use client";

/** Ranking de alcance interactivo: top seleccionable y de dónde viene el índice. */

import { useState } from "react";
import Link from "next/link";
import type { ArtistCard, Followers } from "@/lib/types";
import { PLATAFORMA_COLOR } from "./colores";

const PESOS_LISTA: { clave: keyof Followers; peso: number }[] = [
  { clave: "ig", peso: 0.3 },
  { clave: "fb", peso: 0.25 },
  { clave: "spotify", peso: 0.2 },
  { clave: "yt", peso: 0.1 },
  { clave: "tt", peso: 0.1 },
];

function log10(v: number) {
  return Math.log10(v + 1);
}

function desglose(a: ArtistCard) {
  let total = 0;
  const partes: { clave: string; share: number }[] = [];
  for (const { clave, peso } of PESOS_LISTA) {
    const valor = a.followers[clave] ?? 0;
    const aporte = peso * log10(valor);
    if (aporte > 0) {
      partes.push({ clave, share: aporte });
      total += aporte;
    }
  }
  return partes.map((p) => ({ ...p, share: total ? p.share / total : 0 }));
}

const LIMITES: { valor: number | null; texto: string }[] = [
  { valor: 5, texto: "Top 5" },
  { valor: 10, texto: "Top 10" },
  { valor: 20, texto: "Top 20" },
  { valor: null, texto: "Todos" },
];

export default function RankingInteractivo({
  artistas,
}: {
  artistas: ArtistCard[];
}) {
  const [limite, setLimite] = useState<number | null>(10);
  const [sel, setSel] = useState<string | null>(null);

  const top = artistas
    .filter((a) => a.ranking.indice !== null && a.ranking.indice > 0)
    .sort(
      (a, b) =>
        (b.ranking.indice as number) - (a.ranking.indice as number),
    );
  const visibles = limite === null ? top : top.slice(0, limite);
  const max = Math.max(...visibles.map((a) => a.ranking.indice as number), 1);

  const foco = top.find((a) => a.slug === sel) ?? null;

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-1">
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

      <div className="mb-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
        {PESOS_LISTA.map((p) => (
          <span key={p.clave} className="inline-flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: PLATAFORMA_COLOR[p.clave] }}
            />
            {p.clave.toUpperCase()}
          </span>
        ))}
      </div>

      <div className="flex flex-col gap-2">
        {visibles.map((a) => {
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
                  #{a.ranking.rank}
                </span>
                <Link
                  href={`/artistas/${a.slug}`}
                  onClick={(e) => e.stopPropagation()}
                  className="w-28 shrink-0 truncate text-sm text-muted transition-colors hover:text-accent sm:w-44"
                  title={a.nombre}
                >
                  {a.nombre}
                </Link>
                <div className="flex h-5 flex-1 items-stretch overflow-hidden rounded bg-surface-2">
                  {partes.length > 0 ? (
                    partes.map((p) => (
                      <div
                        key={p.clave}
                        style={{
                          width: `${(p.share * ((a.ranking.indice as number) / max)) * 100}%`,
                          minWidth: p.share > 0.9 ? undefined : 2,
                          backgroundColor:
                            PLATAFORMA_COLOR[p.clave] ?? "var(--accent)",
                        }}
                        title={p.clave.toUpperCase()}
                      />
                    ))
                  ) : (
                    <div
                      className="h-full rounded bg-accent"
                      style={{ width: `${((a.ranking.indice as number) / max) * 100}%` }}
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
            Pasa el cursor o toca una fila para ver de qué redes viene su
            alcance.
          </span>
        )}
      </p>
    </div>
  );
}