import type { Metadata } from "next";
import Link from "next/link";
import { api } from "@/lib/api";
import { fechaCorta } from "@/lib/formato";
import ActividadTemporal from "@/components/stats/ActividadTemporal";
import CiudadesApiladas from "@/components/stats/CiudadesApiladas";
import DonaCategorias from "@/components/stats/DonaCategorias";
import DonaVerificados from "@/components/stats/DonaVerificados";
import EcosistemaRedes from "@/components/stats/EcosistemaRedes";
import EstadoRegistroBarras from "@/components/stats/EstadoRegistroBarras";
import RankingInteractivo from "@/components/stats/RankingInteractivo";

export const metadata: Metadata = {
  title: "Stats de la escena",
  description:
    "Indicadores de la escena de la frontera grande: actividad en el tiempo, ranking de alcance, huella por red, categorías, ciudades y estados.",
};

export const dynamic = "force-dynamic";

const ETIQUETA_ESTADO: Record<string, string> = {
  activo: "Activos",
  en_duda: "En duda",
  inactivo: "Inactivos",
};

export default async function StatsPage() {
  const stats = await api.stats();
  const artistas = await api.artists();

  const total = stats.total;
  const activos = stats.estados["activo"] ?? 0;
  const pctActivos = total ? Math.round((activos / total) * 100) : 0;
  const conRanking = artistas.filter(
    (a) => a.ranking.indice !== null && a.ranking.indice > 0,
  ).length;
  const generos = Object.entries(stats.generos).sort((a, b) => b[1] - a[1]);

  const kpis = [
    { valor: total, etiqueta: "proyectos registrados", color: "var(--accent)" },
    { valor: `${activos}`, etiqueta: `activos (${pctActivos}%)`, color: "var(--activo)" },
    { valor: stats.posts_90dias, etiqueta: "publicaciones en 90 días", color: "var(--en-duda)" },
    { valor: stats.eventos_proximos.total, etiqueta: "eventos próximos", color: "var(--inactivo)" },
  ];

  return (
    <div className="flex flex-col gap-6 lg:gap-8">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl">Stats de la escena</h1>
        <p className="mt-1 text-muted">
          {total} proyectos registrados · {activos} activos ({pctActivos}% de
          la escena).
        </p>
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {kpis.map((k) => (
          <div
            key={k.etiqueta}
            className="rounded-xl border border-line bg-surface p-4 text-center"
          >
            <p className="text-3xl font-bold" style={{ color: k.color }}>
              {k.valor}
            </p>
            <p className="mt-1 text-xs leading-snug text-muted">{k.etiqueta}</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
        <h2 className="mb-1 font-bold">Ranking de alcance</h2>
        <p className="mb-4 text-sm text-muted">
          {conRanking} proyectos con índice calculado. La barra fina muestra de
          qué redes viene el alcance de cada uno.
        </p>
        <RankingInteractivo artistas={artistas} />
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-1 font-bold">Actividad de la escena</h2>
          <p className="mb-4 text-sm text-muted">
            Publicaciones del feed por mes, últimos 12 meses.
          </p>
          <ActividadTemporal serie={stats.feed_serie} />
        </section>

        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-1 font-bold">La base crece</h2>
          <p className="mb-4 text-sm text-muted">
            Proyectos nuevos registrados por mes, últimos 12 meses.
          </p>
          <ActividadTemporal
            serie={stats.altas_por_mes}
            color="var(--activo)"
            rotulo="altas"
          />
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-3 font-bold">Por categoría</h2>
          <DonaCategorias segmentos={stats.segmentos} />
        </section>

        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-3 font-bold">Géneros más presentes</h2>
          <div className="flex flex-wrap gap-2">
            {generos.map(([g, n]) => (
              <span
                key={g}
                className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface-2 px-3 py-1 text-xs"
              >
                <span className="h-2 w-2 rounded-full bg-accent" />
                <span className="text-muted">{g}</span>
                <b className="tabular-nums">{n}</b>
              </span>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-3 font-bold">Salud de la escena</h2>
          <div className="mb-3 flex h-6 overflow-hidden rounded-lg bg-surface-2">
            {(["activo", "en_duda", "inactivo"] as const).map(
              (e) =>
                (stats.estados[e] ?? 0) > 0 && (
                  <div
                    key={e}
                    style={{
                      width: `${((stats.estados[e] ?? 0) / total) * 100}%`,
                      backgroundColor:
                        e === "activo"
                          ? "var(--activo)"
                          : e === "en_duda"
                            ? "var(--en-duda)"
                            : "var(--inactivo)",
                    }}
                  />
                ),
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            {(["activo", "en_duda", "inactivo"] as const).map((e) => (
              <div key={e} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-muted">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{
                      backgroundColor:
                        e === "activo"
                          ? "var(--activo)"
                          : e === "en_duda"
                            ? "var(--en-duda)"
                            : "var(--inactivo)",
                    }}
                  />
                  {ETIQUETA_ESTADO[e]}
                </span>
                <span className="tabular-nums text-text">
                  {stats.estados[e] ?? 0}
                  <span className="ml-1 text-muted">
                    ({total ? Math.round(((stats.estados[e] ?? 0) / total) * 100) : 0}%)
                  </span>
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-1 font-bold">Perfiles verificados</h2>
          <p className="mb-4 text-sm text-muted">
            Proyectos cuyo perfil fue reclamado por el propio artista al
            conectar su página de Facebook/Instagram.
          </p>
          <DonaVerificados
            verificados={stats.verificados}
            total={stats.total}
          />
        </section>

        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-1 font-bold">Procedencia de los perfiles</h2>
          <p className="mb-4 text-sm text-muted">
            Cómo llegó cada proyecto a la base: investigación web, registro
            voluntario o perfil reclamado por el artista.
          </p>
          <EstadoRegistroBarras estados={stats.estados_registro} />
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-3 font-bold">Por ciudad</h2>
          <CiudadesApiladas ciudades={stats.por_ciudad} />
        </section>

        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-3 font-bold">Eventos próximos</h2>
          {stats.eventos_proximos.proximos.length ? (
            <div className="flex flex-col gap-2">
              {stats.eventos_proximos.proximos.map((e) => (
                <div
                  key={`${e.nombre}-${e.fecha}`}
                  className="flex items-center justify-between gap-3 rounded-lg bg-surface-2 px-3 py-2 text-sm"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium">{e.nombre}</p>
                    <p className="text-muted">
                      {e.ciudad}
                      {stats.eventos_proximos.ciudad === e.ciudad &&
                        " · sede principal"}
                    </p>
                  </div>
                  <span className="shrink-0 text-sm tabular-nums text-muted">
                    {fechaCorta(e.fecha)}
                  </span>
                </div>
              ))}
              <Link
                href="/eventos"
                className="text-sm font-semibold text-accent hover:underline"
              >
                Ver todos los eventos →
              </Link>
            </div>
          ) : (
            <p className="text-sm text-muted">Sin eventos programados.</p>
          )}
        </section>
      </div>

      <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
        <h2 className="mb-1 font-bold">Ecosistema de redes</h2>
        <p className="mb-4 text-sm text-muted">
          Audiencia acumulada de la escena y cobertura: cuántos proyectos tienen
          la métrica registrada en la base.
        </p>
        <EcosistemaRedes
          seguidores={stats.seguidores}
          reproducciones={stats.reproducciones}
          cobertura={stats.cobertura}
        />
      </section>
    </div>
  );
}