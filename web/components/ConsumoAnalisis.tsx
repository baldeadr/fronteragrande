"use client";

import { useState } from "react";
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

function RatioEtiqueta({ valor, numero }: { valor: number | null; numero: number }) {
  if (valor === null) return null;
  return (
    <div className="flex items-center justify-between gap-4 border-b border-line/50 pb-1.5 text-sm">
      <span className="text-muted">
        <b className="font-semibold tabular-nums text-text">
          {valor.toLocaleString("es-MX", { maximumFractionDigits: 1 })}×
        </b>{" "}
        {numero === 0 && "vistas de YouTube por suscriptor"}
        {numero === 1 && "oyentes de Spotify por seguidor"}
        {numero === 2 && "seguidores sociales por cada oyente musical"}
      </span>
      <span className="text-xs text-muted">
        {numero === 0 && ">10 indica viralidad"}
        {numero === 1 && ">1 indica descubrimiento activo"}
        {numero === 2 && ">10 indica oportunidad de conversión"}
      </span>
    </div>
  );
}

export default function ConsumoAnalisis({
  consumo,
}: {
  consumo: ConsumoTipo;
}) {
  const [abierto, setAbierto] = useState(false);
  if (consumo.patron === "sin_datos") return null;

  const dominancia = Object.entries(consumo.dominancia);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <span className="font-bold">Consumo: </span>
        <span
          className={`font-bold ${COLOR_PATRON[consumo.patron] ?? "text-muted"}`}
        >
          {ETIQUETAS_PATRON[consumo.patron] ?? consumo.patron}
        </span>

        {dominancia.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {dominancia.slice(0, 4).map(([plataforma, porcentaje]) => {
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

        <button
          type="button"
          onClick={() => setAbierto((v) => !v)}
          className="text-xs font-medium text-accent underline underline-offset-2"
          aria-expanded={abierto}
        >
          {abierto ? "Ocultar análisis" : "Ver análisis"}
        </button>
      </div>

      {abierto && (
        <div className="mt-3 space-y-4 rounded-2xl border border-line bg-surface p-4 sm:p-5">
          <p className="text-sm leading-relaxed text-muted">{consumo.texto}</p>

          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
              Ratios clave
            </h3>
            <div className="space-y-2">
              <RatioEtiqueta valor={consumo.ratios.viralidad_yt} numero={0} />
              <RatioEtiqueta
                valor={consumo.ratios.engagement_spotify}
                numero={1}
              />
              <RatioEtiqueta
                valor={consumo.ratios.gap_social_musica}
                numero={2}
              />
            </div>
          </div>

          {dominancia.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
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
      )}
    </div>
  );
}
