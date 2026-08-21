"use client";

import { useState } from "react";

const TAMANO_LOTE = 6;
import FeedCard from "@/components/FeedCard";
import { fechaCorta } from "@/lib/formato";
import type { EventoArtista, FeedItem } from "@/lib/types";

const PESTANAS = [
  { id: "todo", etiqueta: "Todo", icono: "grid" },
  { id: "posts", etiqueta: "Posts", icono: "texto" },
  { id: "video", etiqueta: "Video", icono: "video" },
  { id: "musica", etiqueta: "Música", icono: "musica" },
  { id: "eventos", etiqueta: "Eventos", icono: "calendario" },
] as const;

type PestanaId = (typeof PESTANAS)[number]["id"];

function IconoPestana({ tipo, className = "" }: { tipo: string; className?: string }) {
  const comun = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  } as const;
  return (
    <svg
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      aria-hidden="true"
      className={className}
      {...comun}
    >
      {tipo === "grid" ? (
        <>
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
        </>
      ) : tipo === "texto" ? (
        <>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </>
      ) : tipo === "video" ? (
        <>
          <path d="m22 8-6 4 6 4V8Z" />
          <rect x="2" y="6" width="14" height="12" rx="2" />
        </>
      ) : tipo === "musica" ? (
        <>
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </>
      ) : (
        <>
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </>
      )}
    </svg>
  );
}

export default function ContenidoPerfil({
  nombre,
  feed,
  eventos,
}: {
  nombre: string;
  feed: FeedItem[];
  eventos: EventoArtista[];
}) {
  const [pestana, setPestana] = useState<PestanaId>("todo");
  const [visible, setVisible] = useState(TAMANO_LOTE);

  const porTipo = (bruto: string) =>
    feed.filter((i) => i.tipo_bruto === bruto);

  const conteos: Record<PestanaId, number> = {
    todo: feed.length,
    posts: porTipo("post").length,
    video: porTipo("video").length,
    musica: porTipo("lanzamiento").length,
    eventos: eventos.length,
  };

  const vacio =
    pestana === "todo"
      ? feed.length === 0
      : pestana === "eventos"
        ? eventos.length === 0
        : conteos[pestana] === 0;

  const mensajeVacio =
    pestana === "eventos"
      ? "No hay eventos registrados todavía."
      : "No hay contenido de este tipo todavía. El contenido aparece cuando el propio artista conecta su cuenta y se sincroniza.";

  const cambiarPestana = (id: PestanaId) => {
    setPestana(id);
    setVisible(TAMANO_LOTE);
  };

  return (
    <section>
      <h2 className="mb-3 text-lg font-bold">
        Contenido de {nombre}
      </h2>

      <div className="mb-4 flex flex-nowrap items-center gap-1">
        {PESTANAS.map((p) => {
          const activo = pestana === p.id;
          return (
            <button
              key={p.id}
              onClick={() => cambiarPestana(p.id)}
              aria-pressed={activo}
              className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-1 text-[11px] font-medium transition-colors sm:px-3 sm:py-1.5 sm:text-xs ${
                activo
                  ? "border-accent bg-accent text-bg"
                  : "border-line bg-surface text-muted hover:text-foreground"
              }`}
            >
              <IconoPestana tipo={p.icono} className="h-3 w-3 shrink-0 sm:h-3.5 sm:w-3.5" />
              {p.etiqueta}
              {conteos[p.id] > 0 && (
                <span className="hidden sm:inline"> ({conteos[p.id]})</span>
              )}
            </button>
          );
        })}
      </div>

      {vacio ? (
        <p className="rounded-xl border border-line bg-surface p-6 text-center text-sm text-muted">
          {mensajeVacio}
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {pestana === "eventos" ? (
            eventos.slice(0, visible).map((e, i) => (
              <div
                key={i}
                className="rounded-xl border border-line bg-surface px-4 py-3"
              >
                <p className="font-medium">{e.nombre}</p>
                <p className="text-xs text-muted">
                  {fechaCorta(e.fecha)}
                  {e.lugar ? ` · ${e.lugar}` : ""}
                  {e.ciudad ? ` · ${e.ciudad}` : ""}
                </p>
              </div>
            ))
          ) : (
            (pestana === "todo"
              ? feed
              : porTipo(
                  pestana === "posts"
                    ? "post"
                    : pestana === "video"
                      ? "video"
                      : "lanzamiento",
                )
            )
              .slice(0, visible)
              .map((item, i) => <FeedCard key={i} item={item} enPerfil />)
          )}
          {conteos[pestana] > visible && (
            <button
              type="button"
              onClick={() => setVisible((v) => v + TAMANO_LOTE)}
              className="mx-auto rounded-lg border border-line px-4 py-2 text-sm text-muted transition-colors hover:text-text"
            >
              Cargar más
            </button>
          )}
        </div>
      )}
    </section>
  );
}