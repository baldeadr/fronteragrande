import type { Metadata } from "next";
import { api } from "@/lib/api";
import { fechaCorta } from "@/lib/formato";
import { banderaEmoji, paisDeCiudad } from "@/lib/ciudades";
import type { Evento } from "@/lib/types";

export const metadata: Metadata = {
  title: "Eventos de la escena",
  description:
    "Eventos, toquines y fiestas de la escena de la frontera grande: fechas, lugares y carteles.",
};

function TarjetaEvento({ e }: { e: Evento }) {
  return (
    <article className="rounded-xl border border-line bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h2 className="font-bold">{e.nombre}</h2>
        {e.fecha && <span className="text-xs text-accent">{fechaCorta(e.fecha)}</span>}
      </div>
      <p className="mt-1 text-sm text-muted">
        {[e.lugar, e.ciudad ? `${e.ciudad} ${banderaEmoji(paisDeCiudad(e.ciudad))}` : null]
          .filter(Boolean)
          .join(" · ") || "Lugar por confirmar"}
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
  );
}

export default async function EventosPage() {
  const eventos = await api.eventos();
  const hoy = new Date().toISOString().slice(0, 10);

  const proximos = eventos
    .filter((e) => e.fecha && e.fecha >= hoy)
    .sort((a, b) => (a.fecha ?? "").localeCompare(b.fecha ?? ""));
  const pasados = eventos
    .filter((e) => !e.fecha || e.fecha < hoy)
    .sort((a, b) => (b.fecha ?? "").localeCompare(a.fecha ?? ""));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl">Eventos</h1>
        <p className="mt-1 text-muted">
          {eventos.length} eventos registrados de la escena de la frontera grande.
          Un evento en el cartel de un artista cuenta como señal de actividad.
        </p>
      </div>

      {eventos.length === 0 ? (
        <p className="rounded-xl border border-line bg-surface p-6 text-center text-muted">
          Aún no hay eventos registrados.
        </p>
      ) : (
        <>
          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold">
              Próximos{" "}
              <span className="text-sm font-normal text-muted">
                ({proximos.length})
              </span>
            </h2>
            {proximos.length === 0 ? (
              <p className="rounded-xl border border-line bg-surface p-6 text-center text-sm text-muted">
                No hay eventos anunciados por ahora.
              </p>
            ) : (
              proximos.map((e) => <TarjetaEvento key={e.id} e={e} />)
            )}
          </section>

          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold">
              Pasados{" "}
              <span className="text-sm font-normal text-muted">
                ({pasados.length})
              </span>
            </h2>
            {pasados.map((e) => (
              <TarjetaEvento key={e.id} e={e} />
            ))}
          </section>
        </>
      )}
    </div>
  );
}
