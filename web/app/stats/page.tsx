import type { Metadata } from "next";
import Link from "next/link";
import { api } from "@/lib/api";
import { fechaCorta } from "@/lib/formato";
import type { ArtistCard } from "@/lib/types";
import { ciudadBase } from "@/lib/ciudades";
import ActividadTemporal from "@/components/stats/ActividadTemporal";
import CiudadesApiladas from "@/components/stats/CiudadesApiladas";
import ComposicionPorCiudad from "@/components/stats/ComposicionPorCiudad";
import CruceLigasGeneros from "@/components/stats/CruceLigasGeneros";
import DonaCategorias from "@/components/stats/DonaCategorias";
import DonaCiudades from "@/components/stats/DonaCiudades";
import DonaVerificados from "@/components/stats/DonaVerificados";
import EcosistemaRedes from "@/components/stats/EcosistemaRedes";
import EstadoRegistroBarras from "@/components/stats/EstadoRegistroBarras";
import RankingFiltrable from "@/components/stats/RankingFiltrable";
import type {
  AtributoDesglose,
  FilaDesglose,
} from "@/components/stats/DesglosePorCiudad";
import {
  GENERO_PALETA,
  NIVEL_COLOR,
  OTRAS_COLOR,
} from "@/components/stats/colores";

export const metadata: Metadata = {
  title: "Stats de la escena",
  description:
    "Indicadores de la escena de la frontera grande: actividad en el tiempo, ranking de alcance, huella por red, categorías, ciudades, ligas y géneros.",
};

const ETIQUETA_ESTADO: Record<string, string> = {
  activo: "Activos",
  en_duda: "En duda",
  inactivo: "Inactivos",
};

const GENEROS_DOMINANTES = Object.keys(GENERO_PALETA);

const LIGAS_ATRIBUTOS: AtributoDesglose[] = Object.keys(NIVEL_COLOR).map(
  (clave) => ({ clave, etiqueta: clave, color: NIVEL_COLOR[clave] }),
);

function desglosePorCiudad(
  artistas: ArtistCard[],
  atributo: (a: ArtistCard) => string | null | undefined,
): FilaDesglose[] {
  const porCiudad = new Map<string, Map<string, number>>();
  for (const a of artistas) {
    const ciudad = ciudadBase(a.ciudad) || "Sin ciudad";
    const clave = atributo(a) || "Sin clasificar";
    if (!porCiudad.has(ciudad)) porCiudad.set(ciudad, new Map());
    const interno = porCiudad.get(ciudad)!;
    interno.set(clave, (interno.get(clave) ?? 0) + 1);
  }
  const filas: FilaDesglose[] = [];
  for (const [ciudad, interno] of porCiudad) {
    const atributos = Object.fromEntries(interno);
    filas.push({
      nombre: ciudad,
      total: Object.values(atributos).reduce((acc, n) => acc + n, 0),
      atributos,
    });
  }
  filas.sort((a, b) => b.total - a.total);
  return filas;
}

export default async function StatsPage() {
  const [stats, artistas] = await Promise.all([api.stats(), api.artists()]);

  const total = stats.total;
  const activos = stats.estados["activo"] ?? 0;
  const pctActivos = total ? Math.round((activos / total) * 100) : 0;
  const escenaLocal = artistas.filter((a) => !a.catalogado);
  const conRanking = escenaLocal.filter(
    (a) => a.ranking.indice !== null && a.ranking.indice > 0,
  ).length;
  const catalogados = artistas.filter((a) => a.catalogado).length;
  const generos = Object.entries(stats.generos).sort((a, b) => b[1] - a[1]);
  const altasEsteMes =
    stats.altas_por_mes[stats.altas_por_mes.length - 1]?.conteo ?? 0;

  const filasLigas = desglosePorCiudad(artistas, (a) =>
    a.catalogado ? a.nivel : "Escena",
  );
  const generosEnDatos = Array.from(
    new Set(artistas.map((a) => a.genero_dominante).filter(Boolean)),
  );
  const generosOrden = [
    ...GENEROS_DOMINANTES,
    ...generosEnDatos.filter((g) => !(g in GENERO_PALETA)),
  ];
  const atributosGenero: AtributoDesglose[] = generosOrden.map((clave) => ({
    clave,
    etiqueta: clave,
    color: GENERO_PALETA[clave] ?? OTRAS_COLOR,
  }));
  const filasGeneros = desglosePorCiudad(
    artistas,
    (a) => a.genero_dominante,
  );

  const matrizLigasGeneros: Record<string, Record<string, number>> = {};
  for (const liga of Object.keys(NIVEL_COLOR)) matrizLigasGeneros[liga] = {};
  for (const a of artistas) {
    const liga = a.catalogado ? a.nivel : "Escena";
    const genero = a.genero_dominante || "Sin clasificar";
    matrizLigasGeneros[liga][genero] =
      (matrizLigasGeneros[liga][genero] ?? 0) + 1;
  }

  const kpis = [
    { valor: total, etiqueta: "proyectos registrados", color: "var(--accent)" },
    { valor: `${activos}`, etiqueta: `activos (${pctActivos}%)`, color: "var(--activo)" },
    { valor: stats.posts_90dias, etiqueta: "publicaciones en 90 días", color: "var(--en-duda)" },
    { valor: altasEsteMes, etiqueta: "altas este mes", color: "var(--inactivo)" },
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
          {conRanking} proyectos de la escena con índice calculado ·{" "}
          {catalogados} en las Ligas. Elige un grupo (o{" "}
          <b>Todos</b>, ordenado por índice universal y con la insignia de Liga
          en cada catalogado) para ver su ranking: la barra fina muestra de qué
          redes viene el alcance de cada uno.
        </p>
        <RankingFiltrable artistas={artistas} />
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
          {stats.ultima_alta && (
            <p className="mt-4 text-sm text-muted">
              Último en sumarse:{" "}
              <Link
                href={`/artistas/${stats.ultima_alta.slug}`}
                className="font-semibold text-accent hover:underline"
              >
                {stats.ultima_alta.nombre}
              </Link>{" "}
              · {fechaCorta(stats.ultima_alta.fecha)}
            </p>
          )}
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
          <h2 className="mb-1 font-bold">Por ciudad</h2>
          <p className="mb-4 text-sm text-muted">
            Cuota porcentual de cada ciudad en la escena y desglose por
            actividad.
          </p>
          <DonaCiudades ciudades={stats.ciudades} limite={8} />
          <hr className="my-5 border-line" />
          <h3 className="mb-3 text-sm font-semibold text-muted">
            Actividad por ciudad
          </h3>
          <CiudadesApiladas ciudades={stats.por_ciudad} />
        </section>

        <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
          <h2 className="mb-1 font-bold">Composición por ciudad</h2>
          <p className="mb-4 text-sm text-muted">
            Qué hay en cada ciudad: cuántos proyectos por liga o por género
            dominante. Cada barra suma 100% de su ciudad; pasa el cursor por
            una barra para ver cantidades y porcentajes.
          </p>
          <ComposicionPorCiudad
            filasLigas={filasLigas}
            atributosLigas={LIGAS_ATRIBUTOS}
            filasGeneros={filasGeneros}
            atributosGeneros={atributosGenero}
          />
        </section>
      </div>

      <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
        <h2 className="mb-1 font-bold">Ligas y géneros</h2>
        <p className="mb-4 text-sm text-muted">
          Cuántos proyectos hay de cada liga según su género dominante (cada
          proyecto cuenta una sola vez). Desliza la tabla hacia los lados si
          es muy ancha.
        </p>
        <CruceLigasGeneros generos={generosOrden} matriz={matrizLigasGeneros} />
      </section>

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
