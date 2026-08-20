import Image from "next/image";
import Link from "next/link";
import type { FeedItem } from "@/lib/types";
import { fechaHora, fechaRelativa } from "@/lib/formato";
import { infoPlataforma } from "./Plataformas";
import IconoRed from "./IconoRed";

export default function FeedCard({
  item,
  enPerfil = false,
}: {
  item: FeedItem;
  enPerfil?: boolean;
}) {
  const esVideo =
    item.preview.tipo === "youtube" ||
    (item.preview.tipo === "tiktok" && item.preview.thumbnail);
  const esSpotify = item.preview.tipo === "spotify" && item.preview.embed_url;
  const alturaSpotify = item.preview.embed_url?.includes("/album/")
    ? "h-[352px]"
    : "h-[152px]";
  const imagen = item.preview.thumbnail ?? "";
  const url = item.url ?? "";
  const fuente = infoPlataforma(item.fuente);
  const inicial = item.artista ? item.artista[0].toUpperCase() : "♪";

  return (
    <article className="flex flex-col gap-3 rounded-2xl border border-line bg-surface p-4 sm:p-5">
      <header className="flex items-center gap-3">
        {item.imagen_artista ? (
          <Image
            src={item.imagen_artista}
            alt={`Foto de ${item.artista}`}
            width={40}
            height={40}
            className="h-10 w-10 shrink-0 rounded-full object-cover"
            unoptimized
          />
        ) : (
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-accent-soft text-lg font-bold text-accent">
            {inicial}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {item.artista ? (
              <Link
                href={`/artistas/${item.artista_slug ?? ""}`}
                className="truncate font-semibold hover:underline"
              >
                {item.artista}
              </Link>
            ) : (
              <span className="truncate font-semibold">Frontera Grande</span>
            )}
            <span title={fuente.nombre}>
              <IconoRed src={fuente.icono} alt={fuente.nombre} size={16} />
            </span>
          </div>
          <p className="text-xs text-muted">
            {fechaHora(item.fecha)}
            {fechaRelativa(item.fecha) && (
              <span className="text-muted/70"> · {fechaRelativa(item.fecha)}</span>
            )}
            {item.tipo ? ` · ${item.tipo}` : ""}
          </p>
        </div>
      </header>

      {(item.titulo || item.detalle) && (
        <div className="flex flex-col gap-1.5">
          {item.titulo && <h3 className="font-semibold leading-snug">{item.titulo}</h3>}
          {item.detalle && (
            <p className="line-clamp-3 text-sm text-muted">{item.detalle}</p>
          )}
        </div>
      )}

      {esSpotify ? (
        <div className="overflow-hidden rounded-xl bg-surface-2">
          <iframe
            src={item.preview.embed_url}
            title={item.titulo}
            className={`${alturaSpotify} w-full border-0`}
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
          />
        </div>
      ) : enPerfil && item.preview.tipo === "youtube" && item.preview.embed_url ? (
        <div className="overflow-hidden rounded-xl bg-surface-2">
          <iframe
            src={item.preview.embed_url}
            title={item.titulo}
            className="aspect-video w-full border-0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            loading="lazy"
          />
        </div>
      ) : esVideo && imagen ? (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="relative block aspect-video w-full overflow-hidden rounded-xl bg-surface-2"
        >
          <Image
            src={imagen}
            alt={item.titulo}
            fill
            sizes="(max-width: 640px) 100vw, 672px"
            className="object-cover"
            unoptimized
          />
          <span className="absolute inset-0 grid place-items-center bg-black/40 text-5xl">
            ▶️
          </span>
        </a>
      ) : item.preview.embed_url && item.preview.tipo !== "mixcloud" ? (
        <div
          className={
            item.preview.tipo === "instagram"
              ? "overflow-hidden rounded-xl bg-surface-2"
              : item.preview.tipo === "facebook"
                ? "overflow-hidden rounded-xl bg-surface-2"
                : "mx-auto aspect-[9/16] w-full max-w-[320px] overflow-hidden rounded-xl bg-surface-2"
          }
        >
          <iframe
            src={item.preview.embed_url}
            className={
              item.preview.tipo === "instagram"
                ? "aspect-[3/4] w-full border-0"
                : item.preview.tipo === "facebook"
                  ? "min-h-[380px] w-full border-0"
                  : "h-full w-full border-0"
            }
            loading="lazy"
            allowFullScreen
            title={item.titulo}
            scrolling="no"
          />
        </div>
      ) : imagen ? (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="relative block aspect-video w-full overflow-hidden rounded-xl bg-surface-2"
        >
          <Image
            src={imagen}
            alt={item.titulo}
            fill
            sizes="(max-width: 640px) 100vw, 672px"
            className="object-cover"
            unoptimized
          />
        </a>
      ) : null}

      {url && (
        <footer className="flex items-center justify-between gap-2">
          {enPerfil ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted hover:text-accent"
            >
              Ver original en {fuente.nombre} →
            </a>
          ) : (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-accent-soft px-3 py-1.5 text-sm font-medium text-accent transition-colors hover:bg-accent hover:text-bg"
            >
              Abrir en {fuente.nombre}
            </a>
          )}
          {enPerfil ? null : item.artista && item.artista_slug && (
            <Link
              href={`/artistas/${item.artista_slug}`}
              className="text-sm text-muted hover:text-accent"
            >
              Ver perfil →
            </Link>
          )}
        </footer>
      )}
    </article>
  );
}
