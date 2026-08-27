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
  distribuido: "text-muted",
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

function RatioFila({
  etiqueta,
  valor,
  unidad,
}: {
  etiqueta: string;
  valor: number | null;
  unidad?: string;
}) {
  if (valor === null) return null;
  return (
    <div className="flex items-center justify-between gap-2 text-sm">
      <span className="text-muted">{etiqueta}</span>
      <span className="font-semibold tabular-nums">
        {valor.toLocaleString("es-MX", { maximumFractionDigits: 1 })}
        {unidad ? ` ${unidad}` : ""}
      </span>
    </div>
  );
}

export default function ConsumoAnalisis({
  consumo,
}: {
  consumo: ConsumoTipo;
}) {
  if (consumo.patron === "sin_datos") return null;

  const dominancia = Object.entries(consumo.dominancia);

  return (
    <div className="rounded-2xl border border-line bg-surface p-4 sm:p-5">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted">
        Hábitos de consumo
      </h2>

      <div className="mb-4">
        <span
          className={`text-sm font-bold ${COLOR_PATRON[consumo.patron] ?? "text-muted"}`}
        >
          {ETIQUETAS_PATRON[consumo.patron] ?? consumo.patron}
        </span>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          {consumo.texto}
        </p>
      </div>

      {(consumo.ratios.viralidad_yt !== null ||
        consumo.ratios.engagement_spotify !== null ||
        consumo.ratios.gap_social_musica !== null) && (
        <div className="mb-4 space-y-1.5">
          <h3 className="text-[11px] font-semibold uppercase tracking-wide text-muted">
            Ratios clave
          </h3>
          <RatioFila
            etiqueta="Viralidad YouTube"
            valor={consumo.ratios.viralidad_yt}
            unidad="vistas/suscr."
          />
          <RatioFila
            etiqueta="Engagement Spotify"
            valor={consumo.ratios.engagement_spotify}
           unidad="oyentes/seg."
          />
          <RatioFila
            etiqueta="Gap social → música"
            valor={consumo.ratios.gap_social_musica}
            unidad="×"
          />
        </div>
      )}

      {dominancia.length > 0 && (
        <div>
          <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted">
            Dominancia por plataforma
          </h3>
          <div className="space-y-2">
            {dominancia.map(([plataforma, porcentaje]) => {
              const info = infoPlataforma(plataforma);
              return (
                <div key={plataforma} className="flex items-center gap-2">
                  <IconoRed src={info.icono} alt={info.nombre} size={14} />
                  <span className="w-20 text-xs text-muted">
                    {NOMBRE_PLATAFORMA[plataforma] ?? plataforma}
                  </span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-line">
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{ width: `${porcentaje}%` }}
                    />
                  </div>
                  <span className="w-12 text-right text-xs font-semibold tabular-nums">
                    {porcentaje}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
