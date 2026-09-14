import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import { FormulaLatex } from "@/components/Formula";
import { IconoLiga } from "@/components/IconoLiga";
import IconoMencion from "@/components/IconoMencion";

export const metadata: Metadata = {
  title: "Acerca de",
  description:
    "Qué es Frontera Grande, la base de datos interactiva de los proyectos musicales de la frontera grande de Tamaulipas: propósito, alcance, límites y cómo se calcula el ranking.",
};

const que_es = [
  "Una base de datos interactiva y pública de los proyectos musicales de la frontera grande de Tamaulipas: bandas, solistas, DJs, colectivos, covers y tributos.",
  "Cada proyecto se descubre, se escucha y se ve en sus redes: previews y enlaces directos (el puente).",
  "Stats de la escena: categorías, ciudades, actividad real y huella digital por plataforma.",
  "Diseñada para crecer: a otras regiones y a otras disciplinas artísticas.",
  "Un impulso a la profesionalización de la escena: la verificación funciona con páginas y cuentas profesionales, y recomendamos a cada proyecto operar con cara de proyecto en redes — no con su perfil personal.",
];

const limites = [
  "No es una plataforma de streaming: no aloja contenido; los previews se abren en su origen.",
  "No es una red social: los perfiles no los administran los artistas, la curaduría la hace el proyecto.",
  "No inventa datos: seguidores, vistas, fechas y logros siempre tienen fuente verificada.",
];

// Matriz de los 10 géneros dominantes con sus familias de subgéneros.
// Fuente de verdad del mapeo: `lib/helpers.py::GENEROS_DOMINANTES`.
const generos = [
  {
    nombre: "Regional",
    color: "#4fa3e8",
    subgeneros:
      "norteño, banda, sierreño, corridos (incl. tumbados y bélicos), tejano/tex-mex, grupero, mariachi, cumbia norteña",
    nota: "polka y conjunto son su herencia europea",
  },
  {
    nombre: "Rock",
    color: "#e4572e",
    subgeneros:
      "alternativo, punk, pop punk, emo, indie, shoegaze, garage, hard rock, progresivo, psicodélico",
    nota: null,
  },
  {
    nombre: "Metal",
    color: "#7d9bb5",
    subgeneros:
      "death, nu metal, industrial, metalcore, hardcore, stoner/doom/sludge, progresivo, post-metal",
    nota: "donde viven muchos covers y tributos",
  },
  {
    nombre: "Urbano",
    color: "#f5a623",
    subgeneros:
      "hip-hop, rap, trap, reggaetón, narco rap, freestyle, R&B",
    nota: null,
  },
  {
    nombre: "EDM",
    color: "#36d6d9",
    subgeneros:
      "house, techno, trance, drum and bass, dubstep, bass house, electrónica",
    nota: null,
  },
  {
    nombre: "Dark",
    color: "#9d4edd",
    subgeneros:
      "post-punk, darkwave, coldwave, gothic rock, synthpop/synthwave, industrial",
    nota: null,
  },
  {
    nombre: "Pop",
    color: "#ff6384",
    subgeneros:
      "pop, latin pop, balada romántica, pop rock",
    nota: null,
  },
  {
    nombre: "Cumbia",
    color: "#1db954",
    subgeneros:
      "cumbia (tropical, villera, sonidera), afrobeat, salsa, reggae, ska, world music",
    nota: null,
  },
  {
    nombre: "Roots",
    color: "#b57edc",
    subgeneros:
      "blues, country, jazz, folk, soul, funk, trova, americana, bluegrass",
    nota: "los géneros que dieron origen al resto",
  },
  {
    nombre: "Experimental",
    color: "#f2c94c",
    subgeneros:
      "noise, drone, ambient, avant-garde/vanguardia, triphop, hyperpop industrial",
    nota: "para el sonido que no cabe en una sola familia",
  },
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
        <div className="flex flex-col gap-2 px-4 pb-4 text-sm leading-relaxed text-muted sm:px-5 sm:pb-5">
          <p>
            Mide el <b>alcance digital</b> de cada proyecto con números reales:
            seguidores, oyentes, reproducciones y vistas.
          </p>
          <p>
            Lo que más pesa es tu <b>mejor plataforma</b> (70 % del puntaje);
            tener presencia en <b>más redes</b> completa el 30 % restante
            (cada plataforma sin dato baja un poco la nota).
          </p>
          <p>
            No compites contra la escena local: todo se mide contra un{" "}
            <b>nivel mundial fijo</b> (lo que logran los artistas grandes). Tu
            puntaje es tuyo y no cambia porque otros crezcan; solo se mueve tu
            lugar si alguien te rebasa.
          </p>
          <p>
            Dos ajustes de la casa: las vistas de YouTube cuentan al{" "}
            <b>60 %</b> (el contador del canal incluye Shorts; la cifra del
            perfil no cambia), y si tus seguidores de IG/FB/TikTok son muy
            altos frente a tu música escuchada, se recortan a{" "}
            <b>consumo × 3</b>: los seguidores comprados no inflan la nota.
          </p>

          <p className="mt-1">
            La fórmula, solo para curiosos: cada número se compara contra su
            tope mundial en escala logarítmica
          </p>
          <div className="overflow-x-auto rounded-xl bg-surface-2 px-4 py-2">
            <FormulaLatex tex="\text{ratio} = \frac{\log_{10}(v+1)}{\log_{10}(\text{techo}+1)}" />
          </div>
          <p>y el puntaje final junta el 70 % de tu mejor plataforma con el 30 % del conjunto:</p>
          <div className="overflow-x-auto rounded-xl bg-surface-2 px-4 py-2">
            <FormulaLatex tex="\text{índice} = 0.7 \cdot \max(\text{ratio}) + 0.3 \cdot \text{media}(\text{ratios})" />
          </div>

          <p>
            <b>¿Qué plataformas cuentan?</b> Instagram, Facebook y TikTok
            (seguidores); YouTube (suscriptores y vistas); Spotify (oyentes
            mensuales); SoundCloud y Bandcamp (reproducciones);
            Beatport y Mixcloud (seguidores). Solo suman las que tienen dato
            real.
          </p>
          <p>
            Tu lugar sale de ese puntaje: el <b>#L</b> es tu puesto dentro de
            tu liga y el <b>#G</b> tu puesto entre todos los proyectos. El
            perfil muestra además un desglose <b>A</b> (audiencia) y <b>C</b>{" "}
            (consumo), pero es solo informativo: el orden siempre lo decide el
            puntaje completo.
          </p>
        </div>
      </details>

      <details className="group rounded-xl border border-line bg-surface" open>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Cómo se clasifican las Ligas
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="flex flex-col gap-2 px-4 pb-4 text-sm leading-relaxed text-muted sm:px-5 sm:pb-5">
          <p>
            La escena se organiza en <b>cuatro ligas</b>: <b>Escena</b> (la
            base, todos los proyectos), <b>Emergente</b>, <b>Ligas Mayores</b>{" "}
            y <b>Leyenda de la Frontera</b>. Cada una tiene su propia
            clasificación y, aparte, un <b>ranking universal</b> que las mide a
            todas a la vez.
          </p>
          <p>
            Son cortes del puntaje explicado arriba (en &quot;Cómo se calcula
            el ranking&quot;):
          </p>
          <p className="flex items-center gap-2">
            <span style={{ color: "#9d4edd" }}>
              <IconoLiga nivel="Escena" className="h-3.5 w-3.5 shrink-0" />
            </span>
            <b>Escena</b> — la base, todos los proyectos sin liga.
          </p>
          <p className="flex items-center gap-2">
            <span style={{ color: "#2fb8a6" }}>
              <IconoLiga nivel="Emergente" className="h-3.5 w-3.5 shrink-0" />
            </span>
            <b>Emergente</b> — puntaje <b>entre 50 y 59</b>: se distingue de la
            base con audiencia y presencia reales.
          </p>
          <p className="flex items-center gap-2">
            <span style={{ color: "#f5b301" }}>
              <IconoLiga nivel="Ligas Mayores" className="h-3.5 w-3.5 shrink-0" />
            </span>
            <b>Ligas Mayores</b> — puntaje <b>≥ 60</b>.
          </p>
          <p className="flex items-center gap-2">
            <span style={{ color: "#aab4c8" }}>
              <IconoLiga
                nivel="Leyenda de la Frontera"
                className="h-3.5 w-3.5 shrink-0"
              />
            </span>
            <b>Leyenda de la Frontera</b> — por curaduría, no por puntaje:
            retirado/a o fallecido/a con legado regional.
          </p>
          <p>
            La posición de cada proyecto sale del mismo puntaje, tanto dentro
            de su liga como entre todos: así la Escena y las Ligas son siempre
            comparables.
          </p>
        </div>
      </details>

      <details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Cómo se clasifican los géneros
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="flex flex-col gap-2 px-4 pb-4 text-sm leading-relaxed text-muted sm:px-5 sm:pb-5">
          <p>
            Cada proyecto tiene un <b>género dominante</b> que resume su sonido.
            Sale automáticamente de los subgéneros que el proyecto declara y se
            agrupan en <b>10 familias</b>. Los casos ambiguos se resuelven por
            curaduría editorial. Algunos géneros colindan de verdad (norteño y
            tex-mex con el country; techno con el industrial), así que se
            adscriben según su familia dominante:
          </p>

          <div className="flex flex-col gap-2">
            {generos.map((g) => (
              <div
                key={g.nombre}
                className="flex items-start gap-2.5 rounded-lg bg-surface-2 px-3 py-2"
              >
                <span
                  className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: g.color }}
                />
                <div className="text-sm leading-relaxed">
                  <b>{g.nombre}</b>
                  <span className="text-muted"> — {g.subgeneros}
                    {g.nota ? ` (${g.nota})` : ""}.
                  </span>
                </div>
              </div>
            ))}
          </div>

          <p>
            Estas familias alimentan el <b>filtro de género</b> del directorio,
            las stats y las insignias del tipo <b>N.º 1 del género</b>.
          </p>
        </div>
      </details>

<details className="group rounded-xl border border-line bg-surface">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 p-4 font-bold sm:p-5">
          Qué son las Insignias y cómo se ganan
          <span className="shrink-0 text-lg leading-none text-accent transition-transform duration-200 group-open:rotate-45">
            +
          </span>
        </summary>
        <div className="flex flex-col gap-3 px-4 pb-4 sm:px-5 sm:pb-5">
          <p className="text-sm leading-relaxed text-muted">
            Dentro de cada liga los proyectos compiten por estas insignias
            (mínimo 3 artistas en el grupo):
          </p>

          <div className="flex flex-wrap gap-2">
            <div className="flex flex-col items-center gap-1 w-[80px]">
              <div className="flex h-[80px] max-h-[80px] min-h-[80px] w-[80px] max-w-[80px] min-w-[80px] shrink-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border p-2 text-center text-[10px] leading-tight border-accent/40 bg-accent-soft/40 text-accent">
                <IconoMencion tipo="categoria" className="h-5 w-5 shrink-0" />
                <span className="line-clamp-3 font-medium">No. 1 Categoría Banda</span>
                <span className="text-[9px] text-muted uppercase">Categoría</span>
              </div>
              <p className="text-[10px] text-muted text-center">Top 1 en su categoría</p>
            </div>
            <div className="flex flex-col items-center gap-1 w-[80px]">
              <div className="flex h-[80px] max-h-[80px] min-h-[80px] w-[80px] max-w-[80px] min-w-[80px] shrink-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border p-2 text-center text-[10px] leading-tight border-accent/40 bg-accent-soft/40 text-accent">
                <IconoMencion tipo="genero" className="h-5 w-5 shrink-0" />
                <span className="line-clamp-3 font-medium">No. 1 en Norteño</span>
                <span className="text-[9px] text-muted uppercase">Género</span>
              </div>
              <p className="text-[10px] text-muted text-center">Top 1 en su género</p>
            </div>
            <div className="flex flex-col items-center gap-1 w-[80px]">
              <div className="flex h-[80px] max-h-[80px] min-h-[80px] w-[80px] max-w-[80px] min-w-[80px] shrink-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border p-2 text-center text-[10px] leading-tight border-accent/40 bg-accent-soft/40 text-accent">
                <IconoMencion tipo="ciudad" className="h-5 w-5 shrink-0" />
                <span className="line-clamp-3 font-medium">No. 1 en Reynosa</span>
                <span className="text-[9px] text-muted uppercase">Ciudad</span>
              </div>
              <p className="text-[10px] text-muted text-center">Top 1 en su ciudad</p>
            </div>
            <div className="flex flex-col items-center gap-1 w-[80px]">
              <div className="flex h-[80px] max-h-[80px] min-h-[80px] w-[80px] max-w-[80px] min-w-[80px] shrink-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border p-2 text-center text-[10px] leading-tight border-en-duda/50 bg-en-duda/10 text-en-duda">
                <IconoMencion tipo="escena" className="h-5 w-5 shrink-0" />
                <span className="line-clamp-3 font-medium">No. 3 Frontera Grande</span>
                <span className="text-[9px] text-muted uppercase">Escena</span>
              </div>
              <p className="text-[10px] text-muted text-center">Top 3 global</p>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-muted">
            Los proyectos de <b>Emergente</b>, <b>Ligas Mayores</b> y{" "}
            <b>Leyenda de la Frontera</b> compiten dentro de su liga y muestran
            además su badge de liga. La <b>Escena</b> (la base) compite entre
            todos sus proyectos.
          </p>
          <p className="text-sm leading-relaxed text-muted">
            Las Ligas se clasifican por <b>alcance verificable</b> (audiencia,
            consumo y actividad), no por ingresos ni por fama del momento.
          </p>
        </div>
      </details>
    </div>
  );
}
