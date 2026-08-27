"use client";

import { infoPlataforma } from "@/components/Plataformas";
import IconoRed from "@/components/IconoRed";
import type { ConsumoAnalisis as ConsumoTipo } from "@/lib/types";

const ETIQUETAS_PATRON: Record<string, string> = {
  youtube_dominante: "YouTube-dominante",
  spotify_dominante: "Spotify-dominante",
  social_dominante: "Social-dominante",
  distribuido: "Distribuido",
  sin_datos: "Sin datos",
};

const COLOR_PATRON: Record<string, string> = {
  youtube_dominante: "text-[#FF0000]",
  spotify_dominante: "text-[#1DB954]",
  social_dominante: "text-accent",
  distribuido: "text-text",
  sin_datos: "text-muted",
};

const NOMBRE_PLATAFORMA: Record<string, string> = {
  ig: "Instagram",
  fb: "Facebook",
  yt: "YouTube",
  tt: "TikTok",
  spotify: "Spotify",
  bandcamp: "Bandcamp",
  soundcloud: "SoundCloud",
  beatport: "Beatport",
  mixcloud: "Mixcloud",
};

function Ratio({ etiqueta, valor }: { etiqueta: string; valor: number | null }) {
  if (valor === null) return null;
  return (
    <span
      className="flex items-center gap-1 text-xs text-muted"
      title={`${etiqueta}: ${valor}`}
    >
      <b className="font-semibold tabular-nums text-text">
        {valor.toLocaleString("es-MX", { maximumFractionDigits: 1 })}×
      </b>
      {etiqueta}
    </span>
  );
}

export default function ConsumoAnalisis({
  consumo,
}: {
  consumo: ConsumoTipo;
}) {
  if (consumo.patron === "sin_datos") return null;

  const dominancia = Object.entries(consumo.dominancia).slice(0, 4);

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
      <span className="font-bold">Consumo: </span>
      <span
        className={`font-bold ${COLOR_PATRON[consumo.patron] ?? "text-muted"}`}
      >
        {ETIQUETAS_PATRON[consumo.patron] ?? consumo.patron}
      </span>

      {dominancia.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {dominancia.map(([plataforma, porcentaje]) => {
            const info = infoPlataforma(plataforma);
            return (
              <span
                key={plataforma}
                className="flex items-center gap-1 rounded-full bg-surface px-2 py-0.5 text-[11px] text-muted"
                title={`${NOMBRE_PLATAFORMA[plataforma] ?? plataforma}: ${porcentaje}%`}
              >
                <IconoRed src={info.icono} alt={info.nombre} size={12} />
                <b className="font-semibold tabular-nums text-text">
                  {porcentaje}%
                </b>
              </span>
            );
          })}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <Ratio etiqueta="viralidad YT" valor={consumo.ratios.viralidad_yt} />
        <Ratio
          etiqueta="engagement Spotify"
          valor={consumo.ratios.engagement_spotify}
        />
        <Ratio
          etiqueta="gap social→música"
          valor={consumo.ratios.gap_social_musica}
        />
      </div>
    </div>
  );
}
