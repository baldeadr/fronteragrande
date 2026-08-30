import Image from "next/image";
import Link from "next/link";
import type { ArtistCard as ArtistCardData } from "@/lib/types";
import EstadoBadge from "./EstadoBadge";
import IconoVerificado from "./IconoVerificado";
import InsigniaNivel from "./InsigniaNivel";
import { abreviaturaDeCiudad, ciudadBase } from "@/lib/ciudades";

export default function ArtistCard({ artist }: { artist: ArtistCardData }) {
  const inicial = artist.nombre ? artist.nombre[0].toUpperCase() : "♪";
  const abrev = artist.ciudad ? abreviaturaDeCiudad(artist.ciudad) : null;

  return (
    <Link
      href={`/artistas/${artist.slug}`}
      className="group relative block aspect-[4/5] overflow-hidden rounded-xl border border-line bg-surface transition-colors hover:border-accent"
    >
      {artist.imagen_perfil ? (
        <Image
          src={artist.imagen_perfil}
          alt={`Foto de ${artist.nombre}`}
          fill
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          className="object-cover transition-transform duration-300 group-hover:scale-105"
          unoptimized
        />
      ) : (
        <div className="grid h-full w-full place-items-center bg-surface-2 text-6xl font-bold text-accent">
          {inicial}
        </div>
      )}

      <div className="absolute inset-0 bg-gradient-to-t from-bg via-bg/60 to-transparent" />

      <div className="absolute right-2 top-2 flex flex-col items-end gap-1">
        <EstadoBadge estado={artist.estado_activo} />
      </div>

      <div className="absolute inset-x-0 bottom-0 flex flex-col gap-2 p-4">
        <h3 className="flex flex-wrap items-center gap-1 text-lg font-bold leading-tight group-hover:text-accent">
          {artist.nombre}
          {artist.verificado && (
            <IconoVerificado
              className="h-4 w-4 shrink-0 text-accent"
              title="Perfil reclamado por el artista"
            />
          )}
        </h3>
        <p className="flex items-center gap-1.5 text-xs text-muted">
          <span className="truncate">
            {artist.segmento}
            {artist.ciudad
              ? ` · ${ciudadBase(artist.ciudad)}${abrev ? ` ${abrev}` : ""}`
              : ""}
          </span>
          {artist.nivel && (
            <InsigniaNivel nivel={artist.nivel} className="shrink-0" />
          )}
        </p>
        <p className="flex flex-wrap gap-1">
          {artist.generos.length === 0 && (
            <span className="text-xs text-muted">Géneros por definir</span>
          )}
          {artist.generos.map((g) => (
            <span
              key={g}
              className="rounded-full bg-accent-soft px-2 py-0.5 text-xs text-accent"
            >
              #{g.replace(/\s+/g, "")}
            </span>
          ))}
        </p>
      </div>
    </Link>
  );
}
