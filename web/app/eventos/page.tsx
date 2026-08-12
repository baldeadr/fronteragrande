import type { Metadata } from "next";
import { api } from "@/lib/api";
import { fechaCorta } from "@/lib/formato";

export const metadata: Metadata = {
  title: "Eventos de la escena",
  description:
    "Eventos, toquines y fiestas de la escena de la frontera grande: fechas, lugares y carteles.",
};

export const dynamic = "force-dynamic";

export default async function EventosPage() {
  const eventos = await api.eventos();

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl">Eventos</h1>
        <p className="mt-1 text-muted">
          {eventos.length} eventos registrados de la escena de la frontera grande.
        </p>
      </div>

      {eventos.length === 0 ? (
        <p className="rounded-xl border border-line bg-surface p-6 text-center text-muted">
          Aún no hay eventos registrados.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {eventos.map((e) => (
            <article
              key={e.id}
              className="rounded-xl border border-line bg-surface p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <h2 className="font-bold">{e.nombre}</h2>
                <span className="text-xs text-accent">
                  {fechaCorta(e.fecha)}
                </span>
              </div>
              <p className="mt-1 text-sm text-muted">
                {[e.lugar, e.ciudad].filter(Boolean).join(" · ") || "Lugar por confirmar"}
              </p>
              {e.artistas && (
                <p className="mt-2 text-sm">
                  <span className="text-muted">Cartel: </span>
                  {e.artistas}
                </p>
              )}
              {e.que_demuestra && (
                <p className="mt-2 text-xs text-muted">{e.que_demuestra}</p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
