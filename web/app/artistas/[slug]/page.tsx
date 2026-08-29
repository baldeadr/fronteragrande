import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import { api } from "@/lib/api";
import EstadoBadge from "@/components/EstadoBadge";
import InsigniaNivel from "@/components/InsigniaNivel";
import Avatar from "@/components/Avatar";
import ContenidoPerfil from "@/components/ContenidoPerfil";
import { infoPlataforma } from "@/components/Plataformas";
import IconoRed from "@/components/IconoRed";
import IconoVerificado from "@/components/IconoVerificado";
import ConexionMeta from "@/components/ConexionMeta";
import ConexionTikTok from "@/components/ConexionTikTok";
import EditarPerfilPropio from "@/components/EditarPerfilPropio";
import IconoMencion from "@/components/IconoMencion";
import BotonEditarAdmin from "@/components/BotonEditarAdmin";
import ConsumoAnalisis from "@/components/ConsumoAnalisis";
import { fechaCorta, fechaCaptura, numeroGrande, tipoStat } from "@/lib/formato";
import { FACEBOOK_FRONTERA_GRANDE } from "@/lib/contacto";

function tipoMencion(
  mencion: string,
): "genero" | "categoria" | "ciudad" | "escena" {
  if (mencion.includes("de la Frontera Grande")) return "escena";
  if (mencion.includes("género")) return "genero";
  if (mencion.includes("categoría")) return "categoria";
  return "ciudad";
}

function esMencionFronteraGrande(mencion: string): boolean {
  return mencion.includes("de la Frontera Grande");
}

function MetricaRanking({
  abreviatura,
  nombre,
  descripcion,
  valor,
}: {
  abreviatura: string;
  nombre: string;
  descripcion: string;
  valor: number | null;
}) {
  return (
    <span
      className="group relative shrink-0 cursor-help text-muted outline-none"
      tabIndex={0}
      title={descripcion}
      aria-label={`${nombre}: ${descripcion}. Valor ${valor ?? "sin dato"}`}
    >
      {abreviatura}{" "}
      <b className="text-text">{valor ?? "-"}</b>
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 w-max max-w-48 -translate-x-1/2 rounded-md bg-surface-2 px-2 py-1 text-[11px] text-text opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus:opacity-100"
      >
        {descripcion}
      </span>
    </span>
  );
}

function etiquetaMetrica(plataforma: string, tipo: string) {
  if (plataforma === "yt" && tipo === "seguidores") return "suscr.";
  if (tipo === "seguidores") return "seg.";
  if (tipo === "vistas") return "vistas";
  if (tipo === "reproducciones") return "reprod.";
  if (tipo === "oyentes_mensuales") return "oyentes/mes";
  return tipo;
}

function etiquetaMetricaCompleta(plataforma: string, tipo: string) {
  if (plataforma === "yt" && tipo === "seguidores") return "suscriptores";
  if (tipo === "vistas") return "vistas totales";
  return tipoStat(tipo);
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  try {
    const artist = await api.artist(slug);
    return {
      title: artist.nombre,
      description: `${artist.nombre} — ${artist.segmento} · ${artist.ciudad}. Escúchalo y síguelo en sus redes.`,
      openGraph: {
        title: `${artist.nombre} · Frontera Grande`,
        description: `${artist.segmento} de ${artist.ciudad} en la escena de la frontera grande.`,
        type: "profile",
        images: [`/artistas/${slug}/opengraph-image.png`],
      },
    };
  } catch {
    return { title: "Artista" };
  }
}

function SeccionFeed({
  nombre,
  feed,
  eventos,
}: {
  nombre: string;
  feed: Awaited<ReturnType<typeof api.artist>>["feed"];
  eventos: Awaited<ReturnType<typeof api.artist>>["eventos"];
}) {
  return (
    <section className="rounded-2xl border border-line bg-surface p-4 sm:p-6">
      <h2 className="mb-3 text-lg font-bold">Contenido reciente</h2>
      <ContenidoPerfil nombre={nombre} feed={feed} eventos={eventos} />
    </section>
  );
}

export default async function PerfilPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ igfb?: string; tiktok?: string }>;
}) {
  const { slug } = await params;
  const { igfb, tiktok } = await searchParams;
  let artist;
  try {
    artist = await api.artist(slug);
  } catch {
    notFound();
  }

  const redes = artist.links.filter((l) => l.url);
  const bio = artist.bio?.trim();

  const stats = Object.entries(artist.stats)
    .map(([plataforma, metricas]) => ({
      plataforma,
      metricas: Object.entries(metricas)
        .filter(([, v]) => typeof v === "number" && v !== null)
        .map(([tipo, valor]) => ({ tipo, valor: valor as number })),
    }))
    .filter((s) => s.metricas.length > 0);

  const infoActividad = [
    artist.metodo_actividad &&
      `Método de actividad: ${artist.metodo_actividad}`,
    artist.ultimo_lanzamiento &&
      `Último lanzamiento: ${fechaCorta(artist.ultimo_lanzamiento)}`,
    artist.ultimo_evento && `Último evento: ${fechaCorta(artist.ultimo_evento)}`,
  ].filter(Boolean);

  return (
    <div className="flex min-w-0 flex-col gap-8 overflow-x-hidden">
      <header className="min-w-0 overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:p-6">
        <div className="flex flex-col gap-6 lg:grid lg:grid-cols-3 lg:items-stretch lg:gap-8">
          <div className="flex flex-col gap-6 lg:col-span-2">
          <div className="flex gap-4 sm:gap-5">
          <Avatar
              src={artist.imagen_perfil}
              nombre={artist.nombre}
              size={160}
              className="h-28 w-28 shrink-0 sm:h-44 sm:w-44"
            />
            <div className="flex min-w-0 flex-1 flex-col gap-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="break-words text-3xl font-bold">
                {artist.nombre}
                {artist.verificado && (
                  <span
                    className="ml-2 inline-flex items-center gap-1 align-middle text-sm font-semibold text-muted"
                    title="Perfil reclamado por el artista: conectó su página de Facebook/Instagram"
                  >
                    <IconoVerificado className="h-4 w-4 text-accent" />
                    Verificado
                  </span>
                )}
                {artist.es_propio && (
                  <span
                    className="ml-2 rounded-full bg-accent px-2 py-0.5 text-xs font-semibold text-bg align-middle"
                    title="Proyecto del propio universo"
                  >
                    Propio
                  </span>
                )}
                {artist.nivel && (
                  <span className="ml-2 align-middle">
                    <InsigniaNivel nivel={artist.nivel} />
                  </span>
                )}
              </h1>
              <p className="mt-1 text-muted">
                {artist.segmento}
                {artist.ciudad ? ` · ${artist.ciudad}` : ""}
              </p>
            </div>
            <EstadoBadge estado={artist.estado_activo} size="lg" />
            <BotonEditarAdmin slug={artist.slug} />
            <EditarPerfilPropio
              slug={artist.slug}
              nombre={artist.nombre}
              ciudad={artist.ciudad}
              categoria={artist.segmento}
              generos={artist.generos}
              bio={artist.bio}
              logros={artist.logros}
              redes={redes
                .filter((l) => !l.es_busqueda)
                .map((l) => ({ plataforma: l.plataforma, url: l.url }))}
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            {artist.generos.length === 0 && (
              <span className="text-xs text-muted">Géneros por definir</span>
            )}
            {artist.generos.map((g) => (
              <span
                key={g}
                className="rounded-full bg-accent-soft px-3 py-1 text-xs font-medium text-accent"
              >
                #{g.replace(/\s+/g, "")}
              </span>
            ))}
          </div>

          <p className="whitespace-pre-line text-sm text-muted">
            {bio || "[PENDIENTE] — pendiente de redactar."}
          </p>

          {infoActividad.length > 0 && (
            <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted">
              {infoActividad.map((linea) => (
                <span key={linea}>{linea}</span>
              ))}
            </div>
          )}

          {redes.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              {redes.map((l) => {
                const p = infoPlataforma(l.plataforma);
                return (
                  <a
                    key={l.url}
                    href={l.url}
                    target={l.plataforma === "email" ? undefined : "_blank"}
                    rel={l.plataforma === "email" ? undefined : "noopener noreferrer"}
                    aria-label={p.nombre}
                    className="group relative grid h-11 w-11 place-items-center rounded-full border border-line bg-surface/80 transition-colors hover:border-accent"
                  >
                    <IconoRed src={p.icono} alt={p.nombre} size={20} />
                    <span className="pointer-events-none absolute -top-9 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-md bg-surface-2 px-2 py-1 text-xs opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                      {p.nombre}
                    </span>
                  </a>
                );
              })}
            </div>
          )}
          </div>
          </div>

          <div className="mb-3 pb-2">
            <ConsumoAnalisis consumo={artist.consumo} />
          </div>

          {(() => {
              // Filtrar menciones: excluir "Frontera Grande" para Ligas Mayores y En Ascenso
              const mencionesFiltradas = artist.menciones.filter((m) => {
                if (esMencionFronteraGrande(m)) {
                  return !["Ligas Mayores", "En Ascenso"].includes(artist.nivel || "");
                }
                return true;
              });

              return mencionesFiltradas.length > 0 ? (
                <div className="border-t border-line/50 pt-3">
                  <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted">
                    Menciones especiales
                  </h2>
                  {artist.nivel && (
                    <div className="mb-3 flex items-center gap-2 rounded-lg border border-line bg-surface p-3">
                      <div className="flex items-center gap-2">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-2">
                          {artist.nivel === "Ligas Mayores" && (
                            <svg className="h-5 w-5 text-[#f5b301]" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                            </svg>
                          )}
                          {artist.nivel === "En Ascenso" && (
                            <svg className="h-5 w-5 text-[#2fb8a6]" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M7 14l5-5 5 5z"/>
                            </svg>
                          )}
                          {artist.nivel === "Leyenda de la Frontera" && (
                            <svg className="h-5 w-5 text-[#8a63d2]" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9H15V22H9V9H3L12 3L21 9Z"/>
                            </svg>
                          )}
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-muted">Liga</p>
                          <p className="font-bold text-sm">{artist.nivel}</p>
                        </div>
                      </div>
                    </div>
                  )}
                  <ul className="flex flex-wrap gap-2">
                    {mencionesFiltradas.map((m) => {
                      const esEscena = tipoMencion(m) === "escena";
                      return (
                        <li
                          key={m}
                          title={m}
                          className={`flex h-[80px] max-h-[80px] min-h-[80px] w-[80px] max-w-[80px] min-w-[80px] shrink-0 flex-col items-center justify-center gap-1 overflow-hidden rounded-xl border p-2 text-center text-[10px] leading-tight ${
                            esEscena
                              ? "border-en-duda/50 bg-en-duda/10 font-medium text-en-duda"
                              : "border-accent/40 bg-accent-soft/40 text-accent"
                          }`}
                        >
                          <IconoMencion
                            tipo={tipoMencion(m)}
                            className="h-5 w-5 shrink-0"
                          />
                          <span className="line-clamp-3">{m}</span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : null;
            })()}
        </div>

        {stats.length > 0 && (
          <div className="flex flex-col border-t border-line/50 pt-6 lg:col-span-1 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
            <div className="mb-3 flex items-baseline justify-between gap-3">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-muted">
                Estadísticas en redes
              </h2>
              {artist.fecha_captura && (
                <span className="shrink-0 text-[10px] text-muted">
                  Actualizado {fechaCaptura(artist.fecha_captura)}
                </span>
              )}
            </div>
            {artist.ranking.indice !== null && artist.ranking.rank !== null && (
              <div className="mb-3 overflow-visible rounded-2xl border border-accent/40 bg-accent-soft/60 p-3">
                <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 text-[10px] sm:gap-3 sm:text-xs">
                  <span className="shrink-0 font-semibold uppercase tracking-wide text-muted">
                    Ranking
                  </span>
                  <b className="text-base">
                    #{artist.ranking.rank}
                  </b>
                  <MetricaRanking
                    abreviatura="G"
                    nombre="Global"
                    descripcion="Combinación de audiencia y consumo"
                    valor={artist.ranking.indice}
                  />
                  <MetricaRanking
                    abreviatura="A"
                    nombre="Audiencia"
                    descripcion="Tamaño relativo de la comunidad"
                    valor={artist.ranking.audiencia}
                  />
                  <MetricaRanking
                    abreviatura="C"
                    nombre="Consumo"
                    descripcion="Reproducciones, oyentes y vistas registradas"
                    valor={artist.ranking.consumo}
                  />
                </div>
              </div>
            )}
            <div className="grid auto-rows-[112px] grid-cols-2 gap-3 sm:grid-cols-2">
              {stats.map((s) => {
                const p = infoPlataforma(s.plataforma);
                return (
                  <div
                    key={s.plataforma}
                    className="flex h-full min-w-0 flex-col justify-between gap-2 overflow-hidden rounded-2xl border border-line bg-surface p-3"
                  >
                    <div className="flex items-center gap-2 text-xs text-muted">
                      <IconoRed src={p.icono} alt={p.nombre} size={18} />
                      <span className="truncate font-medium">{p.nombre}</span>
                    </div>
                    <div className="flex flex-1 flex-wrap items-center gap-x-3 gap-y-2">
                      {s.metricas.map((m) => (
                        <div key={m.tipo} className="flex items-start gap-1.5">
                          <p
                            className="text-xl font-bold tabular-nums sm:text-2xl"
                            title={`${m.valor.toLocaleString("es-MX")} ${etiquetaMetricaCompleta(
                              s.plataforma,
                              m.tipo,
                            )}${artist.fecha_captura ? ` · capturado ${fechaCorta(artist.fecha_captura)}` : ""}`}
                          >
                            {numeroGrande(m.valor)}
                          </p>
                          <div className="flex flex-col pt-0.5 text-[11px] leading-tight text-muted">
                            <span
                              className="font-medium"
                              title={etiquetaMetricaCompleta(s.plataforma, m.tipo)}
                            >
                              {etiquetaMetrica(s.plataforma, m.tipo)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        </div>
      </header>

      {igfb === "ok" && (
        <p className="rounded-lg border border-activo/40 bg-surface px-3 py-2 text-sm text-activo">
          Perfil verificado. Tus posts de Facebook/Instagram se sincronizan
          automáticamente; la actualización se refleja en unas horas.
        </p>
      )}
      {igfb === "desconectado" && (
        <p className="rounded-lg border border-activo/40 bg-surface px-3 py-2 text-sm text-activo">
          Cuenta de Meta desvinculada. Se detuvo la sincronización de nuevas
          publicaciones; el contenido histórico permanece en el feed.
        </p>
      )}
      {igfb === "error" && (
        <div className="rounded-lg border border-inactivo/40 bg-surface px-3 py-2 text-sm text-inactivo">
          <p>
            No se pudo conectar la cuenta. Asegúrate de autorizar con la cuenta
            que administra la página de Facebook registrada e intenta de nuevo.
          </p>
          <Link href="/ayuda-artistas" className="mt-1 inline-block underline">
            Consulta la ayuda para artistas
          </Link>
        </div>
      )}

      {tiktok === "ok" && (
        <p className="rounded-lg border border-activo/40 bg-surface px-3 py-2 text-sm text-activo">
          Cuenta de TikTok conectada. Tus seguidores y videos se sincronizarán
          automáticamente; la actualización se refleja en unas horas.
        </p>
      )}
      {tiktok === "error" && (
        <div className="rounded-lg border border-inactivo/40 bg-surface px-3 py-2 text-sm text-inactivo">
          <p>
            No se pudo conectar TikTok. Autoriza con la cuenta que administra el
            perfil registrado e intenta de nuevo.
          </p>
        </div>
      )}

      {(artist.igfb.configurado || artist.tiktok.configurado) && (
        <details className="group rounded-2xl border border-line bg-surface p-4">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2">
            <span className="text-sm font-medium text-muted">
              {artist.verificado
                ? `¿Administras ${artist.nombre}? Conecta tus redes`
                : `¿Eres ${artist.nombre}? Conecta tus redes para verificar tu perfil`}
            </span>
            <span
              aria-hidden
              className="text-xs text-muted transition-transform group-open:rotate-180"
            >
              ▾
            </span>
          </summary>

          <div className="mt-3 flex flex-col gap-4">
            <Link
              href="/ayuda-artistas"
              className="text-xs text-accent hover:underline"
            >
              ¿Cómo funciona la verificación?
            </Link>

            {artist.igfb.configurado && (
              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium">Meta</p>
                  <p className="text-xs text-muted">
                    {artist.igfb.conectado
                      ? `Conectado · sincroniza tus publicaciones de Facebook e Instagram${
                          artist.igfb.pagina_fb
                            ? ` (${artist.igfb.pagina_fb})`
                            : ""
                        }`
                      : "Verifica tu perfil y sincroniza tus publicaciones de Facebook e Instagram."}
                  </p>
                </div>
                <ConexionMeta
                  slug={artist.slug}
                  conectado={artist.igfb.conectado}
                />
              </div>
            )}

            {artist.tiktok.configurado && (
              <div className="flex min-w-0 items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium">TikTok</p>
                  <p className="text-xs text-muted">
                    {artist.tiktok.conectado
                      ? "Conectado · sincroniza tus seguidores y videos"
                      : "Conecta para sincronizar tus seguidores y videos."}
                  </p>
                </div>
                <ConexionTikTok
                  slug={artist.slug}
                  conectado={artist.tiktok.conectado}
                />
              </div>
            )}
          </div>
        </details>
      )}

      <p className="text-xs text-muted">
        ¿Ves un dato incorrecto en este perfil?{" "}
        <a
          href={FACEBOOK_FRONTERA_GRANDE}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent underline underline-offset-2"
        >
          Repórtalo por Facebook
        </a>
      </p>

      <Suspense
        fallback={
          <div className="rounded-2xl border border-line bg-surface p-4 sm:p-6">
            <h2 className="mb-3 text-lg font-bold">Contenido reciente</h2>
            <div className="flex min-h-[8rem] items-center justify-center">
              <span className="h-6 w-6 animate-spin rounded-full border-2 border-line border-t-accent" />
            </div>
          </div>
        }
      >
        <SeccionFeed
          nombre={artist.nombre}
          feed={artist.feed}
          eventos={artist.eventos}
        />
      </Suspense>
    </div>
  );
}
