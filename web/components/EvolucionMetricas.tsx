"use client";

/**
 * Evolución mensual de los números de un artista.
 *
 * Tarjeta discreta (<details>) bajo el hero, con el mismo patrón que los
 * botones de conectar redes: el usuario casual la ignora y solo quien quiere
 * estudiar el caso la abre. Todo es público (democratizar: ver qué le
 * funcionó al otro). Dentro: una sola gráfica SVG de estilo relativo
 * (100% = inicio de la ventana) para comparar plataformas de distinta
 * magnitud, con filtro de rango (3M/6M/12M/Todo) y de métrica, y marcas de
 * hitos (lanzamiento, videoclip, toquín) sobre las fechas en que pasaron.
 */

import { useMemo, useState } from "react";
import IconoRed from "@/components/IconoRed";
import { infoPlataforma } from "@/components/Plataformas";
import { PLATAFORMA_COLOR } from "@/components/stats/colores";
import { etiquetaMes, mesCorto, numeroGrande, tipoStat } from "@/lib/formato";
import type { EvolucionMetricas, Hito, PuntoMetrica } from "@/lib/types";

const VENTANAS: { clave: number; etiqueta: string }[] = [
  { clave: 3, etiqueta: "3M" },
  { clave: 6, etiqueta: "6M" },
  { clave: 12, etiqueta: "12M" },
  { clave: 0, etiqueta: "Todo" },
];

const HITO_COLOR: Record<string, string> = {
  lanzamiento: "#f5b301",
  videoclip: "#b57edc",
  "toquín": "#4fa3e8",
};

const ANCHO = 640;
const ALTO = 210;
const PAD = { arriba: 16, abajo: 6, izq: 10, der: 10 };

function etiquetaChip(metrica: string): string {
  if (metrica === "seguidores") return "Seguidores";
  if (metrica === "vistas") return "Vistas";
  if (metrica === "reproducciones") return "Reproducciones";
  if (metrica === "oyentes_mensuales") return "Oyentes/mes";
  return metrica;
}

type SerieVentana = {
  plataforma: string;
  base: number;
  puntos: { mes: string; valor: number; relativo: number; primera: boolean }[];
};

function datosDeVentana(
  historial: EvolucionMetricas["historial"],
  metrica: string,
  meses: string[],
): SerieVentana[] {
  const series: SerieVentana[] = [];
  for (const [plataforma, metricas] of Object.entries(historial)) {
    const puntos = metricas[metrica];
    if (!puntos || puntos.length === 0) continue;
    const mapa = new Map(puntos.map((p) => [p.mes, p]));
    const enVentana = meses
      .filter((m) => mapa.has(m))
      .map((m) => mapa.get(m) as PuntoMetrica);
    if (enVentana.length === 0) continue;
    const base = enVentana[0].valor || 1;
    series.push({
      plataforma,
      base,
      puntos: enVentana.map((p) => ({
        mes: p.mes,
        valor: p.valor,
        relativo: (p.valor / base) * 100,
        primera: p.primera_captura,
      })),
    });
  }
  return series;
}

export default function EvolucionMetricas({
  datos,
}: {
  datos: EvolucionMetricas | null;
}) {
  const [ventana, setVentana] = useState(6);
  const [metricaSel, setMetricaSel] = useState<string | null>(null);

  const { historial, hitos } = useMemo(
    () => ({ historial: datos?.historial ?? {}, hitos: datos?.hitos ?? [] }),
    [datos],
  );

  const tiposDisponibles = useMemo(() => {
    const tipos = new Set<string>();
    for (const metricas of Object.values(historial)) {
      for (const metrica of Object.keys(metricas)) tipos.add(metrica);
    }
    return ["seguidores", "vistas", "oyentes_mensuales", "reproducciones"].filter(
      (t) => tipos.has(t),
    );
  }, [historial]);

  const metrica = metricaSel ?? tiposDisponibles[0] ?? null;

  const meses: string[] = useMemo(() => {
    if (!metrica) return [];
    let primero: string | null = null;
    for (const metricas of Object.values(historial)) {
      const puntos = metricas[metrica];
      if (puntos && puntos.length > 0) {
        const m = puntos[0].mes;
        if (!primero || m < primero) primero = m;
      }
    }
    if (!primero) return [];
    const [ay, am] = primero.split("-").map(Number);
    const ahora = new Date();
    const [by, bm] = [ahora.getFullYear(), ahora.getMonth() + 1];
    const lista: string[] = [];
    let y = ay;
    let m = am;
    while (y < by || (y === by && m <= bm)) {
      lista.push(`${y}-${String(m).padStart(2, "0")}`);
      m += 1;
      if (m > 12) {
        m = 1;
        y += 1;
      }
    }
    if (ventana > 0 && lista.length > ventana) {
      return lista.slice(lista.length - ventana);
    }
    return lista;
  }, [historial, metrica, ventana]);

  const series = useMemo(
    () => (metrica ? datosDeVentana(historial, metrica, meses) : []),
    [historial, metrica, meses],
  );

  const hitosPorMes = useMemo(() => {
    const agrupados = new Map<string, Hito[]>();
    if (ventana > 0 && meses.length > 0) {
      const desde = meses[0];
      for (const h of hitos) {
        if (h.fecha.slice(0, 7) >= desde) {
          const lista = agrupados.get(h.fecha.slice(0, 7)) ?? [];
          lista.push(h);
          agrupados.set(h.fecha.slice(0, 7), lista);
        }
      }
    }
    return agrupados;
  }, [hitos, ventana, meses]);

  if (!metrica || series.length === 0) return null;

  // Geometría de la gráfica.
  const rel = series.flatMap((s) => s.puntos.map((p) => p.relativo));
  let dMax = Math.max(100, ...rel);
  let dMin = Math.min(100, ...rel);
  if (dMax - dMin < 1) {
    dMax += 1;
    dMin -= 1;
  }
  const n = meses.length;
  const anchoUtil = ANCHO - PAD.izq - PAD.der;
  const altoUtil = ALTO - PAD.arriba - PAD.abajo;
  const x = (i: number) =>
    n > 1
      ? PAD.izq + (i / (n - 1)) * anchoUtil
      : PAD.izq + anchoUtil / 2;
  const y = (v: number) =>
    PAD.arriba + ((dMax - v) / (dMax - dMin)) * altoUtil;
  const yBase = y(100);

  return (
    <details className="group mt-6 overflow-hidden rounded-2xl border border-line bg-surface">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-4 py-4">
        <span className="text-sm font-medium text-muted">
          Números · evolución mes a mes
        </span>
        <span
          aria-hidden
          className="text-xs text-muted transition-transform group-open:rotate-180"
        >
          ▾
        </span>
      </summary>

      <div className="flex flex-col gap-3 border-t border-line/50 px-4 pb-4 pt-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-1.5">
            {tiposDisponibles.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setMetricaSel(t)}
                className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
                  t === metrica
                    ? "border-accent/60 bg-accent-soft/40 text-accent"
                    : "border-line text-muted hover:text-text"
                }`}
              >
                {etiquetaChip(t)}
              </button>
            ))}
          </div>
          <div className="flex gap-1.5">
            {VENTANAS.map((v) => (
              <button
                key={v.clave}
                type="button"
                onClick={() => setVentana(v.clave)}
                className={`rounded-full border px-2.5 py-1 text-xs tabular-nums transition-colors ${
                  v.clave === ventana
                    ? "border-accent/60 bg-accent-soft/40 text-accent"
                    : "border-line text-muted hover:text-text"
                }`}
              >
                {v.etiqueta}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {series.map((s) => (
            <span
              key={s.plataforma}
              className="flex items-center gap-1.5 text-xs text-muted"
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: PLATAFORMA_COLOR[s.plataforma] ?? "var(--accent)" }}
              />
              <IconoRed
                src={infoPlataforma(s.plataforma).icono}
                alt={infoPlataforma(s.plataforma).nombre}
                size={14}
              />
              <b className="text-text tabular-nums">
                {numeroGrande(s.puntos[s.puntos.length - 1].valor)}
              </b>
            </span>
          ))}
        </div>

        <div className="mt-1 overflow-x-auto">
          <svg
            viewBox={`0 0 ${ANCHO} ${ALTO}`}
            className="min-w-[520px] w-full"
            role="img"
            aria-label={`Evolución de ${etiquetaChip(metrica).toLowerCase()} por mes`}
          >
            {/* Hitos: línea vertical en el mes donde hay evento registrado. */}
            {hitosPorMes.size > 0 &&
              meses.map((m, i) => {
                const grupo = hitosPorMes.get(m);
                if (!grupo) return null;
                const xv = x(i);
                const titulo = grupo
                  .map((h) => `${HITO_COLOR[h.tipo] ? h.tipo : "hito"}: ${h.titulo}`)
                  .join(" · ");
                return (
                  <g key={m}>
                    <line
                      x1={xv}
                      y1={PAD.arriba}
                      x2={xv}
                      y2={ALTO - PAD.abajo}
                      stroke="var(--muted)"
                      strokeOpacity={0.35}
                      strokeDasharray="3 3"
                    />
                    <circle cx={xv} cy={PAD.arriba - 5} r={3} fill="var(--muted)">
                      <title>{`${etiquetaMes(m)} · ${titulo}`}</title>
                    </circle>
                  </g>
                );
              })}

            {/* Línea base: 100% (inicio de la ventana). */}
            <line
              x1={PAD.izq}
              y1={yBase}
              x2={ANCHO - PAD.der}
              y2={yBase}
              stroke="var(--muted)"
              strokeOpacity={0.4}
              strokeDasharray={n > 1 ? "2 4" : "0"}
            />
            {n > 1 && (
              <text
                x={PAD.izq}
                y={yBase - 4}
                fill="var(--muted)"
                fontSize={9}
              >
                100% inicio
              </text>
            )}

            {/* Líneas por plataforma (relativo al inicio de la ventana). */}
            {series.map((s) => {
              const color = PLATAFORMA_COLOR[s.plataforma] ?? "var(--accent)";
              return (
                <g key={s.plataforma}>
                  <polyline
                    points={s.puntos
                      .map(
                        (p) =>
                          `${x(meses.indexOf(p.mes)).toFixed(1)},${y(p.relativo).toFixed(1)}`,
                      )
                      .join(" ")}
                    fill="none"
                    stroke={color}
                    strokeWidth={2}
                    strokeLinejoin="round"
                    strokeLinecap="round"
                    strokeOpacity={0.9}
                  >
                    <title>{infoPlataforma(s.plataforma).nombre}</title>
                  </polyline>
                  {s.puntos.map((p) => {
                    const xp = x(meses.indexOf(p.mes));
                    const yp = y(p.relativo);
                    const variacion =
                      s.base > 0
                        ? ` (${Math.round((p.relativo - 100) * 10) / 10 >= 0 ? "+" : ""}${(Math.round(p.relativo * 10) / 10 - 100).toFixed(1)}%)`
                        : "";
                    const titulo = `${infoPlataforma(s.plataforma).nombre} · ${etiquetaMes(
                      p.mes,
                    )} · ${p.valor.toLocaleString("es-MX")} ${tipoStat(
                      metrica,
                    )}${variacion}${
                      p.primera ? " · primeras datos: el registro nace al conectar la cuenta" : ""
                    }`;
                    return (
                      <circle
                        key={`${s.plataforma}-${p.mes}`}
                        cx={xp}
                        cy={yp}
                        r={p.primera ? 4 : 2.5}
                        fill={color}
                        stroke={p.primera ? "var(--bg)" : "none"}
                        strokeWidth={p.primera ? 1.5 : 0}
                        className="cursor-pointer"
                      >
                        <title>{titulo}</title>
                      </circle>
                    );
                  })}
                </g>
              );
            })}
          </svg>
        </div>

        <div className="flex gap-px">
          {meses.map((m) => (
            <span
              key={m}
              className="flex-1 text-center text-[10px] uppercase text-muted"
            >
              {mesCorto(m)}
            </span>
          ))}
        </div>

        <p className="text-[11px] text-muted">
          Comparación relativa (100% = inicio de la ventana). Las líneas{" "}
          punteadas son hitos conocidos con su fecha:{" "}
          <span className="text-text">lanzamiento</span> ·{" "}
          <span className="text-text">videoclip</span> ·{" "}
          <span className="text-text">toquín</span>. En IG/FB/TikTok el
          registro nace al conectar la cuenta.
        </p>
      </div>
    </details>
  );
}