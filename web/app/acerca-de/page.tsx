import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import { FormulaInline, FormulaLatex } from "@/components/Formula";
import IconoRed from "@/components/IconoRed";
import { infoPlataforma } from "@/components/Plataformas";

export const metadata: Metadata = {
  title: "Acerca de",
  description:
    "Qué es Frontera Grande, la base de datos interactiva de los proyectos musicales de la frontera grande de Tamaulipas: propósito, alcance, límites y cómo se calcula el ranking.",
};

const pesos = [
  { clave: "ig", plataforma: "Instagram", peso: "0,29" },
  { clave: "fb", plataforma: "Facebook", peso: "0,24" },
  { clave: "spotify", plataforma: "Spotify · seguidores", peso: "0,0475" },
  { clave: "spotify", plataforma: "Spotify · consumo", peso: "0,1425" },
  { clave: "yt", plataforma: "YouTube · suscriptores", peso: "0,027" },
  { clave: "yt", plataforma: "YouTube · vistas", peso: "0,063" },
  { clave: "tt", plataforma: "TikTok", peso: "0,09" },
  { clave: "bandcamp", plataforma: "Bandcamp", peso: "0,025" },
  { clave: "soundcloud", plataforma: "SoundCloud", peso: "0,025" },
  { clave: "beatport", plataforma: "Beatport", peso: "0,03" },
  { clave: "mixcloud", plataforma: "Mixcloud", peso: "0,02" },
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
      <section className="flex flex-row items-center gap-4 rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:gap-5 sm:p-8">
        <Image
          src="/logo-frontera-grande.svg"
          alt="Frontera Grande"
          width={112}
          height={112}
          className="shrink-0 rounded-xl"
        />
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
          <b>Adrian Balderas</b> llamado{" "}
          <a
            href="https://baldeadr.github.io/architecting-a-band-web/"
            target="_blank"
            rel="noopener noreferrer"
            className="font-bold text-accent hover:underline"
          >
            architecting-a-band
          </a>
          .
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
                  key={`${p.clave}-${p.peso}`}
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
            El ranking separa dos señales (0–100): <b>audiencia</b> para
            seguidores y suscriptores, y <b>consumo</b> para oyentes,
            reproducciones y vistas. Cada señal se transforma con logaritmo y se
            normaliza frente al máximo de su métrica. El índice global combina
            ambos: 55% audiencia y 45% consumo.
          </p>

          <div className="mt-2 overflow-x-auto rounded-xl bg-surface-2 px-4 py-3">
            <FormulaLatex
              tex="I_s = 0.55 I_{audiencia} + 0.45 I_{consumo}"
            />
          </div>

          <ul className="mt-3 flex flex-col gap-2">
            <li className="flex gap-2.5 text-sm leading-relaxed text-muted">
              <span className="text-accent">·</span>En YouTube, el consumo pesa
              70% de su componente y los suscriptores 30%.
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

      <details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Cómo se clasifican las Ligas
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="flex flex-col gap-2 px-4 pb-4 sm:px-5 sm:pb-5">
          <p className="text-sm leading-relaxed text-muted">
            Algunos proyectos destacan por su alcance o su legado y se
            catalogan en una <b>Liga</b>. Estos no participan en el ranking de
            la escena local (para no desbalancearlo); se muestran en una
            gráfica aparte.
          </p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: "#f5b301" }}
            />
            <b>Ligas Mayores</b> — una red con ≥ 1 millón de seguidores, o ≥ 1
            millón de oyentes en Spotify, o entrada a charts
            nacionales/internacionales con fuente.
          </p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: "#2fb8a6" }}
            />
            <b>En Ascenso</b> — suma de señales con fuente entre 10 mil y
            999 mil (seguidores, oyentes, reproducciones y vistas).
          </p>
          <p className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: "#8a63d2" }}
            />
            <b>Leyenda de la Frontera</b> — retirado/a o fallecido/a con un
            legado en la región; se asigna por curaduría, no por métricas.
          </p>
        </div>
      </details>

<details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Qué son las Insignias y cómo funcionan
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="flex flex-col gap-2 px-4 pb-4 sm:px-5 sm:pb-5">
          <p className="text-sm leading-relaxed text-muted">
            En el perfil de cada artista hay una sección <b>Insignias</b> que
            reconoce su posición en la escena. Funcionan con <b>mutua exclusión</b>:
          </p>

          <div className="flex flex-wrap gap-3 mb-2">
            <div className="inline-flex items-center gap-2 rounded-xl border p-2 bg-surface-2 text-[#f5b301]">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
              <span className="font-medium text-xs">Ligas Mayores</span>
            </div>
            <div className="inline-flex items-center gap-2 rounded-xl border p-2 bg-surface-2 text-[#2fb8a6]">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M7 14l5-5 5 5z"/></svg>
              <span className="font-medium text-xs">En Ascenso</span>
            </div>
            <div className="inline-flex items-center gap-2 rounded-xl border p-2 bg-surface-2 text-[#8a63d2]">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9H15V22H9V9H3L12 3L21 9Z"/></svg>
              <span className="font-medium text-xs">Leyenda</span>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-muted">
            Los tres niveles de Liga (ver <b>«Cómo se clasifican las Ligas»</b>
            arriba) son <b>exclusivos</b>: un artista con Liga <b>solo muestra
            su badge de Liga</b> (no acumula insignias de categoría, género,
            ciudad ni <b>Nº X de la Frontera Grande</b>).
          </p>
          <p className="text-sm leading-relaxed text-muted">
            Los artistas <b>sin Liga</b> compiten por insignias de ranking:
            categoría, género, ciudad y <b>Nº X de la Frontera Grande</b>.
            Así la meta es alcanzable: quien no tiene Liga aún puede brillar en
            su categoría/ciudad/género.
          </p>

          <div className="flex flex-wrap gap-2 mt-2 text-xs text-muted">
            <span className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-1">
              <span className="h-3 w-3 rounded-full bg-accent"></span> Categoría
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-1">
              <span className="h-3 w-3 rounded-full bg-accent"></span> Género
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-1">
              <span className="h-3 w-3 rounded-full bg-accent"></span> Ciudad
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-line bg-surface px-2 py-1">
              <span className="h-3 w-3 rounded-full bg-en-duda"></span> Escena
            </span>
          </div>
        </div>
      </details>
    </div>
  );
}
