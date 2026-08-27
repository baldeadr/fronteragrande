import Link from "next/link";
import IconoVerificado from "@/components/IconoVerificado";

interface HeroActividadProps {
  stats: {
    total: number;
    estados: Record<string, number>;
    verificados: number;
  };
}

export default function HeroActividad({ stats }: HeroActividadProps) {
  return (
    <section className="rounded-2xl border border-line bg-gradient-to-br from-accent-soft to-surface p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold leading-tight sm:text-2xl">
            Actividad de la escena
          </h1>
          <p className="mt-1 text-sm text-muted max-w-2xl hidden sm:block">
            Lo que publican los proyectos de la frontera grande de Tamaulipas en sus
            redes: videos, lanzamientos y eventos.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-muted">
          <span>
            <b className="text-lg text-text">{stats.total}</b> proyectos
            registrados
          </span>
          <span>
            <b className="text-lg text-activo">{stats.estados["activo"] ?? 0}</b>{" "}
            activos
          </span>
          <span className="inline-flex items-center gap-1.5">
            <IconoVerificado className="h-4 w-4 text-accent" />
            <b className="text-lg text-text">{stats.verificados}</b> verificados
          </span>
          <Link
            href="/artistas"
            className="ml-2 rounded-lg bg-accent px-3 py-1.5 text-sm font-semibold text-bg transition-opacity hover:opacity-90"
          >
            Ver directorio →
          </Link>
        </div>
      </div>
    </section>
  );
}