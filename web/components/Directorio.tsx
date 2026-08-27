"use client";

import { useMemo, useState } from "react";
import type { ArtistCard as ArtistCardData } from "@/lib/types";
import ArtistCard from "./ArtistCard";

export default function Directorio({
  artistas,
  busquedaInicial = "",
}: {
  artistas: ArtistCardData[];
  busquedaInicial?: string;
}) {
  const [q, setQ] = useState(busquedaInicial);
  const [segmento, setSegmento] = useState("todos");
  const [ciudad, setCiudad] = useState("todos");
  const [estado, setEstado] = useState("todos");
  const [generosSel, setGenerosSel] = useState<string[]>([]);
  const [generosExpandidos, setGenerosExpandidos] = useState(false);

  const segmentos = useMemo(
    () => [...new Set(artistas.map((a) => a.segmento))].sort(),
    [artistas],
  );
  const ciudades = useMemo(
    () =>
      [...new Set(artistas.map((a) => a.ciudad).filter(Boolean))].sort(),
    [artistas],
  );
  const generos = useMemo(
    () =>
      [...new Set(artistas.flatMap((a) => a.generos))].sort(),
    [artistas],
  );

  const filtrados = useMemo(() => {
    const ql = q.toLowerCase().trim();
    return artistas.filter((a) => {
      if (segmento !== "todos" && a.segmento !== segmento) return false;
      if (ciudad !== "todos" && a.ciudad !== ciudad) return false;
      if (estado !== "todos" && a.estado_activo !== estado) return false;
      if (generosSel.length > 0 && !generosSel.some((g) => a.generos.includes(g)))
        return false;
      if (ql) {
        const texto = `${a.nombre} ${a.generos.join(" ")}`.toLowerCase();
        if (!texto.includes(ql)) return false;
      }
      return true;
    });
  }, [artistas, q, segmento, ciudad, estado, generosSel]);

  function alternarGenero(g: string) {
    setGenerosSel((actual) =>
      actual.includes(g) ? actual.filter((x) => x !== g) : [...actual, g],
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar…"
          className="col-span-2 self-end rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent sm:col-span-3 lg:col-span-2"
        />
        <div className="flex flex-col gap-1">
          <label htmlFor="filtro-categoria" className="text-xs font-medium text-muted">
            Categoría
          </label>
          <select
            id="filtro-categoria"
            value={segmento}
            onChange={(e) => setSegmento(e.target.value)}
            className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
          >
            <option value="todos">Todas</option>
            {segmentos.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="filtro-ciudad" className="text-xs font-medium text-muted">
            Ciudad
          </label>
          <select
            id="filtro-ciudad"
            value={ciudad}
            onChange={(e) => setCiudad(e.target.value)}
            className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
          >
            <option value="todos">Todas</option>
            {ciudades.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="filtro-actividad" className="text-xs font-medium text-muted">
            Actividad
          </label>
          <select
            id="filtro-actividad"
            value={estado}
            onChange={(e) => setEstado(e.target.value)}
            className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
          >
            <option value="todos">Todas</option>
            <option value="activo">Activo</option>
            <option value="en_duda">En duda</option>
            <option value="inactivo">Inactivo</option>
          </select>
        </div>
      </div>

      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        <li className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--activo)" }} />
          <span className="font-medium text-foreground">Activo:</span> actividad en los últimos 6 meses
        </li>
        <li className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--en-duda)" }} />
          <span className="font-medium text-foreground">En duda:</span> actividad entre 6 y 18 meses, o sin registros
        </li>
        <li className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--inactivo)" }} />
          <span className="font-medium text-foreground">Inactivo:</span> sin actividad en más de 18 meses, o pausa
        </li>
      </ul>

      {generos.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Géneros</span>
            <button
              type="button"
              onClick={() => setGenerosExpandidos(!generosExpandidos)}
              className="text-xs text-accent hover:underline"
              aria-expanded={generosExpandidos}
            >
              {generosExpandidos ? "Ver menos" : "Ver más"}
            </button>
          </div>
          <div
            className="flex flex-wrap gap-1.5"
            style={{
              maxHeight: generosExpandidos ? "none" : "48px",
              overflow: "hidden",
              transition: "max-height 0.2s ease",
            }}
          >
            <button
              onClick={() => setGenerosSel([])}
              aria-pressed={generosSel.length === 0}
              className={`rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                generosSel.length === 0
                  ? "border-accent bg-accent text-bg"
                  : "border-line bg-surface text-muted hover:text-foreground"
              }`}
            >
              Todos
            </button>
            {generos.map((g) => {
              const activo = generosSel.includes(g);
              return (
                <button
                  key={g}
                  onClick={() => alternarGenero(g)}
                  aria-pressed={activo}
                  className={`rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                    activo
                      ? "border-accent bg-accent text-bg"
                      : "border-line bg-surface text-muted hover:text-foreground"
                  }`}
                >
                  {g}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <p className="text-sm text-muted">
        {filtrados.length} de {artistas.length} proyectos
      </p>

      {filtrados.length === 0 ? (
        <p className="rounded-xl border border-line bg-surface p-6 text-center text-muted">
          Sin resultados para esos filtros.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtrados.map((a) => (
            <ArtistCard key={a.slug} artist={a} />
          ))}
        </div>
      )}
    </div>
  );
}
