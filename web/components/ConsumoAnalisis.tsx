"use client";

import { useState } from "react";
import { infoPlataforma } from "@/components/Plataformas";
import IconoRed from "@/components/IconoRed";
import type { ConsumoAnalisis as ConsumoTipo } from "@/lib/types";

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

const ETIQUETA_PATRON: Record<string, string> = {
  instagram_dominante: "Instagram-dominante",
  facebook_dominante: "Facebook-dominante",
  tiktok_dominante: "TikTok-dominante",
  youtube_dominante: "YouTube-dominante",
  spotify_dominante: "Spotify-dominante",
  beatport_dominante: "Beatport-dominante",
  mixcloud_dominante: "Mixcloud-dominante",
  bandcamp_dominante: "Bandcamp-dominante",
  soundcloud_dominante: "SoundCloud-dominante",
  distribuido: "Distribuido",
  sin_datos: "Sin datos",
};

const ETIQUETA_BALANCE: Record<string, string> = {
  consumo_dominante: "Consumo mayor que audiencia",
  inclinado_consumo: "Ligado al consumo",
  equilibrado: "Audiencia y consumo equilibrados",
  inclinado_social: "Ligado a la audiencia",
  social_dominante: "Audiencia mayor que consumo",
  parcial: "Señal incompleta",
  sin_datos: "Sin datos suficientes",
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

function Dimension({
  titulo,
  patron,
  dominancia,
}: {
  titulo: string;
  patron: string;
  dominancia: Record<string, number>;
}) {
  const entradas = Object.entries(dominancia);
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
        {titulo}
        {patron && patron !== "sin_datos" && patron !== "distribuido" && (
          <span className="ml-2 normal-case text-accent">
            · {ETIQUETA_PATRON[patron] ?? patron}
          </span>
        )}
      </h3>
      {entradas.length === 0 ? (
        <p className="text-sm text-muted">Sin datos suficientes.</p>
      ) : (
        <div className="space-y-2">
          {entradas.map(([plataforma, porcentaje]) => {
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
      )}
    </div>
  );
}

export default function ConsumoAnalisis({
  consumo,
}: {
  consumo: ConsumoTipo;
}) {
  const [abierto, setAbierto] = useState(false);
  const datosConsumo = consumo.consumo?.dominancia ?? {};
  const datosAudiencia = consumo.audiencia?.dominancia ?? {};
  const sinDatos = Object.keys(datosConsumo).length === 0 && Object.keys(datosAudiencia).length === 0;
  if (sinDatos) return null;

  const tieneDatos = Object.keys(datosConsumo).length > 0 || Object.keys(datosAudiencia).length > 0;

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <span className="font-bold">Análisis: </span>
        <span className="font-bold text-text">
          {ETIQUETA_BALANCE[consumo.balance] ?? "Análisis"}
        </span>

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

          {tieneDatos ? (
            <>
              <Dimension
                titulo="Consumo (reproducciones y vistas)"
                patron={consumo.consumo.patron}
                dominancia={consumo.consumo.dominancia}
              />
              <Dimension
                titulo="Audiencia (seguidores)"
                patron={consumo.audiencia.patron}
                dominancia={consumo.audiencia.dominancia}
              />

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
            </>
          ) : (
            <p className="text-sm text-muted">
              Conecta tus plataformas y añade enlaces de streaming para que el
              análisis compare tu consumo y tu audiencia.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
