import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { FormulaInline, FormulaLatex } from "@/components/Formula";
import IconoRed from "@/components/IconoRed";
import { infoPlataforma } from "@/components/Plataformas";

export const metadata: Metadata = {
  title: "Acerca de",
  description:
    "Qué es Frontera Grande, la base de datos interactiva de los proyectos musicales de la frontera grande de Tamaulipas: propósito, alcance, límites y cómo se calcula el ranking.",
};

const pesos = [
  { clave: "ig", plataforma: "Instagram", peso: "0,30" },
  { clave: "fb", plataforma: "Facebook", peso: "0,25" },
  { clave: "spotify", plataforma: "Spotify", peso: "0,20" },
  { clave: "yt", plataforma: "YouTube", peso: "0,10" },
  { clave: "tt", plataforma: "TikTok", peso: "0,10" },
  { clave: "bandcamp", plataforma: "Bandcamp", peso: "0,025" },
  { clave: "soundcloud", plataforma: "SoundCloud", peso: "0,025" },
];

const que_es = [
  "Una base de datos interactiva y pública de los proyectos musicales de la frontera grande de Tamaulipas: bandas, solistas, DJs, colectivos, covers y tributos.",
  "Cada proyecto se descubre, se escucha y se ve en sus redes: previews y enlaces directos (el puente).",
  "Stats de la escena: categorías, ciudades, actividad real y huella digital por plataforma.",
  "Diseñada para crecer: a otras regiones y a otras disciplinas artísticas.",
];

const limites = [
  "No es una plataforma de streaming: no aloja contenido; los previews se abren en su origen.",
  "No es una red social: los perfiles no los administran los artistas, la curaduría la hace el proyecto.",
  "No inventa datos: seguidores, vistas, fechas y logros siempre tienen fuente verificada.",
];

const paginas = [
  {
    href: "/",
    icono: "feed",
    nombre: "Actividad",
    descripcion:
      "la bitácora de la escena: los videos, lanzamientos y eventos que publican los proyectos, y sus números.",
  },
  {
    href: "/artistas",
    icono: "directorio",
    nombre: "Directorio",
    descripcion:
      "busca y filtra por categoría, ciudad o género; cada proyecto tiene sus redes, previews y ranking.",
  },
  {
    href: "/eventos",
    icono: "eventos",
    nombre: "Eventos",
    descripcion: "los próximos conciertos y presentaciones de la frontera grande.",
  },
  {
    href: "/stats",
    icono: "stats",
    nombre: "Stats",
    descripcion:
      "métricas por plataforma, ranking de alcance y menciones de la escena.",
  },
];

const iconosPagina: Record<string, ReactNode> = {
  directorio: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="7" height="7" rx="1" />
      <rect x="13" y="4" width="7" height="7" rx="1" />
      <rect x="4" y="13" width="7" height="7" rx="1" />
      <rect x="13" y="13" width="7" height="7" rx="1" />
    </svg>
  ),
  feed: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 12h2l2-6 3 12 2-8 2 4h5" />
    </svg>
  ),
  eventos: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 9h18" />
      <path d="M8 3v4M16 3v4" />
    </svg>
  ),
  stats: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 20v-6" />
      <path d="M12 20V9" />
      <path d="M19 20v-9" />
      <path d="M3 20h18" />
    </svg>
  ),
};

export default function AcercaDePage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:p-8">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-xl text-bg">
          ♪
        </span>
        <div>
          <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
            Acerca de Frontera Grande
          </h1>
          <p className="mt-1 max-w-2xl text-muted">
            La base de datos interactiva de la escena musical de la frontera
            grande de Tamaulipas. Esto es lo que somos, lo que hacemos y lo que
            no hacemos.
          </p>
        </div>
      </section>

      <section className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6">
        <span className="text-xs font-bold tracking-wider text-accent">
          La historia
        </span>
        <p className="text-sm leading-relaxed text-muted">
          Frontera Grande nació de la necesidad de investigar la competencia
          local y entender cómo encajar en ella. Con el tiempo, esa idea pivotó
          y tomó forma como base de datos interactiva abierta a todo el público.
          Hoy Frontera Grande forma parte del universo artístico de{" "}
          <b>Adrian Balderas</b> llamado <b>architecting-a-band</b>.
        </p>
      </section>

      <section className="flex flex-col gap-3 rounded-xl border border-line bg-surface p-5 sm:p-6">
        <span className="text-xs font-bold tracking-wider text-accent">
          Cómo explorar la plataforma
        </span>
        <div className="grid gap-2 sm:grid-cols-2">
          {paginas.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              className="flex items-center gap-3 rounded-lg border border-line bg-surface-2 px-3 py-2.5 transition-colors hover:border-accent"
            >
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent">
                <span className="h-5 w-5">{iconosPagina[p.icono]}</span>
              </span>
              <span className="flex flex-col gap-0.5">
                <span className="text-sm font-bold">{p.nombre}</span>
                <span className="text-sm leading-relaxed text-muted">
                  {p.descripcion}
                </span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      <details className="group rounded-xl border border-line bg-surface" open>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Qué es
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <ul className="flex flex-col gap-2 px-4 pb-4 sm:px-5 sm:pb-5">
          {que_es.map((q) => (
            <li
              key={q}
              className="flex gap-2.5 rounded-lg bg-surface-2 px-3 py-2 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">—</span>
              {q}
            </li>
          ))}
        </ul>
      </details>

      <details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Qué no es
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <ul className="flex flex-col gap-2 px-4 pb-4 sm:px-5 sm:pb-5">
          {limites.map((l) => (
            <li
              key={l}
              className="flex gap-2.5 rounded-lg bg-surface-2 px-3 py-2 text-sm leading-relaxed text-muted"
            >
              <span className="text-accent">—</span>
              {l}
            </li>
          ))}
        </ul>
      </details>

      <details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Cómo se calcula la actividad
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="flex flex-col gap-2 px-4 pb-4 text-sm leading-relaxed text-muted sm:px-5 sm:pb-5">
          <p>
            La señal sale de internet: sus publicaciones en redes, videos y
            eventos, rastreados automáticamente.
          </p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: "var(--activo)" }}
            />
            <b>Activo</b> — actividad en los últimos 6 meses.
          </p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: "var(--en-duda)" }}
            />
            <b>En duda</b> — actividad entre 6 y 18 meses, o sin señal
            suficiente.
          </p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: "var(--inactivo)" }}
            />
            <b>Inactivo</b> — sin actividad en más de 18 meses, o pausa
            confirmada.
          </p>
        </div>
      </details>

      <details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Cómo se calcula el ranking
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="px-4 pb-4 sm:px-5 sm:pb-5">
          <p className="text-sm leading-relaxed text-muted">
            Mide el <b>alcance digital</b> de cada proyecto. Por cada plataforma
            se usa su métrica de alcance (seguidores, reproducciones o vistas),
            se transforma con <FormulaInline tex="\log_{10}(v+1)" /> y cada una
            pesa distinto:
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {pesos.map((p) => {
              const icono = infoPlataforma(p.clave).icono;
              return (
                <span
                  key={p.plataforma}
                  className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs"
                >
                  <IconoRed src={icono} alt={p.plataforma} size={14} />
                  <b>{p.plataforma}</b>{" "}
                  <span className="tabular-nums text-muted">{p.peso}</span>
                </span>
              );
            })}
          </div>

          <p className="mt-4 text-sm leading-relaxed text-muted">
            El índice <FormulaInline tex="I_s" /> (0–100) es la suma ponderada del
            alcance de cada plataforma, normalizado por el máximo de esa
            plataforma entre todos los artistas de la base:
          </p>

          <div className="mt-2 overflow-x-auto rounded-xl bg-surface-2 px-4 py-3">
            <FormulaLatex
              tex="I_s = 100 \sum_{p \in P} w_p \; \frac{\log_{10}(v_{s,p} + 1)}{\max_{t \in A} \log_{10}(v_{t,p} + 1)}"
            />
          </div>

          <ul className="mt-3 flex flex-col gap-2">
            <li className="flex gap-2.5 text-sm leading-relaxed text-muted">
              <span className="text-accent">·</span>Sin esa plataforma (o con
              métrica 0), su alcance es 0: la ausencia penaliza.
            </li>
            <li className="flex gap-2.5 text-sm leading-relaxed text-muted">
              <span className="text-accent">·</span>Si el máximo de una
              plataforma es 0 (nadie la tiene), esa plataforma no aporta al
              índice.
            </li>
            <li className="flex gap-2.5 text-sm leading-relaxed text-muted">
              <span className="text-accent">·</span>El rango ordena de mayor a
              menor, y la mención &quot;Nº 1&quot; destaca al máximo en cada
              grupo (género, ciudad y categoría).
            </li>
          </ul>
        </div>
      </details>
    </div>
  );
}