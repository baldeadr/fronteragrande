"use client";

/** Ranking de alcance con filtros por grupo: la Escena (base) y las Ligas.
 *  Re-ranquea 1..N dentro del grupo seleccionado; la posición oficial de la
 *  API no cambia (esa se ve en el perfil del artista). */

import { useState } from "react";
import Link from "next/link";
import type { ArtistCard } from "@/lib/types";
import { IconoLiga, INFO_LIGAS } from "@/components/IconoLiga";
import { ciudadBase } from "@/lib/ciudades";

const GRUPO_COLOR = { audiencia: "var(--accent)", consumo: "#f5a623" };

// Orden estable de los 10 géneros dominantes del catálogo (coincide con la
// taxonomía de `lib.helpers.GENEROS_DOMINANTES` del backend).
const GENEROS_DOMINANTES = [
  "Regional",
  "Rock",
  "Metal",
  "Urbano",
  "EDM",
  "Dark",
  "Pop",
  "Cumbia",
  "Roots",
  "Experimental",
];

const COLOR_NIVEL: Record<string, string> = {
  "Ligas Mayores": "#f5b301",
  Emergente: "#2fb8a6",
  "Leyenda de la Frontera": "#aab4c8",
};

type ClaveGrupo =
  | "todos"
  | "escena"
  | "ligas_mayores"
  | "emergente"
  | "leyenda";

const GRUPOS: {
  clave: ClaveGrupo;
  etiqueta: string;
  color: string;
  icono: string | null;
  seleccionar: (a: ArtistCard) => boolean;
}[] = [
  {
    clave: "todos",
    etiqueta: "Todos",
    color: "var(--text)",
    icono: null,
    seleccionar: () => true,
  },
  {
    clave: "escena",
    etiqueta: "Escena",
    color: "var(--accent)",
    icono: "Escena",
    seleccionar: (a) => !a.catalogado,
  },
  {
    clave: "ligas_mayores",
    etiqueta: "Ligas Mayores",
    color: COLOR_NIVEL["Ligas Mayores"],
    icono: "Ligas Mayores",
    seleccionar: (a) => a.nivel === "Ligas Mayores",
  },
  {
    clave: "emergente",
    etiqueta: "Emergente",
    color: COLOR_NIVEL["Emergente"],
    icono: "Emergente",
    seleccionar: (a) => a.nivel === "Emergente",
  },
  {
    clave: "leyenda",
    etiqueta: "Leyenda",
    color: COLOR_NIVEL["Leyenda de la Frontera"],
    icono: "Leyenda de la Frontera",
    seleccionar: (a) => a.nivel === "Leyenda de la Frontera",
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
  const [generoSel, setGeneroSel] = useState<string>("");
  const [ciudadSel, setCiudadSel] = useState<string>("");

  const generosDisponibles = GENEROS_DOMINANTES.filter((g) =>
    artistas.some((a) => a.genero_dominante === g),
  );
  const ciudadesDisponibles = [
    ...new Set(
      artistas
        .map((a) => ciudadBase(a.ciudad))
        .filter((c) => c && c !== "[PENDIENTE]"),
    ),
  ].sort();

  const grupoActivo = GRUPOS.find((g) => g.clave === grupo)!;
  const miembros = artistas
    .filter(grupoActivo.seleccionar)
    .filter((a) => !generoSel || a.genero_dominante === generoSel)
    .filter((a) => !ciudadSel || ciudadBase(a.ciudad) === ciudadSel);
  // Se ordena por el índice universal (comparable entre todas las ligas) en
  // todos los grupos: así cada liga muestra su clasificación real derivada del
  // índice universal (coincide con `rank_liga` del perfil).
  const valorOrden = (a: ArtistCard) => a.ranking.indice_universal ?? 0;
  const conIndice = miembros
    .filter((a) => {
      const v = valorOrden(a);
      return v !== null && v > 0;
    })
    .sort((a, b) => valorOrden(b) - valorOrden(a));
  const sinIndice =
    grupo === "todos"
      ? miembros.filter((a) => {
          const v = valorOrden(a);
          return !v || v <= 0;
        })
      : [];
  const visibles =
    grupo === "todos"
      ? limite === null
        ? [...conIndice, ...sinIndice]
        : conIndice.slice(0, limite)
      : limite === null
        ? conIndice
        : conIndice.slice(0, limite);
  const max = Math.max(...visibles.map((a) => valorOrden(a)), 1);
  const foco = conIndice.find((a) => a.slug === sel) ?? null;
  const esLiga = grupo !== "escena" && grupo !== "todos";

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
              {g.icono ? (
                <span style={{ color: g.color }}>
                  <IconoLiga nivel={g.icono} className="h-3.5 w-3.5" />
                </span>
              ) : (
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: g.color }}
                />
              )}
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
        {generosDisponibles.length > 0 && (
          <select
            value={generoSel}
            onChange={(e) => setGeneroSel(e.target.value)}
            className="rounded-full border border-line bg-surface-2 px-2.5 py-1 text-xs text-muted outline-none focus:border-accent"
            aria-label="Filtrar por género dominante"
          >
            <option value="">Todos los géneros</option>
            {generosDisponibles.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        )}
        {ciudadesDisponibles.length > 0 && (
          <select
            value={ciudadSel}
            onChange={(e) => setCiudadSel(e.target.value)}
            className="rounded-full border border-line bg-surface-2 px-2.5 py-1 text-xs text-muted outline-none focus:border-accent"
            aria-label="Filtrar por ciudad"
          >
            <option value="">Todas las ciudades</option>
            {ciudadesDisponibles.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        )}
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

      {conIndice.length + sinIndice.length === 0 ? (
        <p className="text-sm text-muted">
          Aún no hay proyectos con índice calculado en este grupo.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {visibles.map((a, i) => {
            const partes = desglose(a);
            const activo = sel === a.slug;
            const indice = valorOrden(a);
            const tienenIndice = indice > 0;
            return (
              <div
                key={a.slug}
                onMouseEnter={() => setSel(a.slug)}
                onMouseLeave={() => setSel(null)}
                onClick={() => setSel(activo ? null : a.slug)}
                className="cursor-pointer rounded-lg border border-transparent px-1 py-1 transition-colors hover:border-line"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-8 shrink-0 text-sm font-bold ${
                      tienenIndice ? "text-accent" : "text-muted"
                    }`}
                  >
                    {tienenIndice ? `#${i + 1}` : "—"}
                  </span>
                  <div className="flex w-28 shrink-0 items-center gap-1 sm:w-40">
                    <Link
                      href={`/artistas/${a.slug}`}
                      onClick={(e) => e.stopPropagation()}
                      className="min-w-0 flex-1 truncate text-sm text-muted transition-colors hover:text-accent"
                      title={a.nombre}
                    >
                      {a.nombre}
                    </Link>
                    {(esLiga || grupo === "todos") && a.catalogado && (
                      <span
                        className="inline-flex shrink-0 items-center"
                        style={{ color: INFO_LIGAS[a.nivel] ?? "#888" }}
                        title={`Liga: ${a.nivel}`}
                      >
                        <IconoLiga nivel={a.nivel} className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </div>
                  <div className="flex h-5 flex-1 items-stretch overflow-hidden rounded bg-surface-2">
                    {tienenIndice && partes.length > 0 ? (
                      partes.map((p) => (
                        <div
                          key={p.clave}
                          style={{
                            width: `${
                              (p.share * (indice / max)) * 100
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
                          width: `${indice === 0 ? 0 : (indice / max) * 100}%`,
                          opacity: tienenIndice ? 1 : 0,
                        }}
                      />
                    )}
                  </div>
                  <span className="w-9 shrink-0 text-right text-sm font-medium tabular-nums text-muted">
                    {tienenIndice ? indice : "—"}
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
            <b>{foco.nombre}</b> · índice universal{" "}
            {foco.ranking.indice_universal ?? 0} de{" "}
            {foco.ranking.total_universal ?? foco.ranking.total}:{" "}
            {desglose(foco)
              .map((p) => `${p.clave.toUpperCase()} ${Math.round(p.share * 100)}%`)
              .join(", ")}
          </span>
        ) : (
          <span className="text-xs">
            Pasa el cursor o toca una fila para ver la proporción de audiencia
            y consumo · posiciones por índice universal (comparable entre todas
            las ligas) · filtra por género dominante y ciudad si lo deseas.
          </span>
        )}
      </p>
    </div>
  );
}