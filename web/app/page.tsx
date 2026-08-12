import Link from "next/link";
import { api } from "@/lib/api";
import FeedLista from "@/components/FeedLista";
import IconoVerificado from "@/components/IconoVerificado";

export default async function Home() {
  const [stats, feed] = await Promise.all([api.stats(), api.feed()]);

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-5 sm:p-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
              Actividad de la escena
            </h1>
            <p className="mt-1 max-w-2xl text-muted">
Lo que publican los proyectos de la frontera grande de Tamaulipas en sus redes:
                videos, lanzamientos y eventos.
            </p>
          </div>
          <Link
            href="/artistas"
            className="rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition-opacity hover:opacity-90"
          >
            Ver directorio →
          </Link>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted">
          <span>
            <b className="text-xl text-text">{stats.total}</b> proyectos
            registrados
          </span>
          <span>
            <b className="text-xl text-activo">{stats.estados["activo"] ?? 0}</b>{" "}
            activos
          </span>
          <span className="inline-flex items-center gap-1.5">
            <IconoVerificado className="h-4 w-4 text-accent" />
            <b className="text-xl text-text">{stats.verificados}</b> verificados
          </span>
        </div>
      </section>

      <FeedLista items={feed} />
    </div>
  );
}
