"use client";

/** Alta, edición y baja de eventos del calendario desde el panel de admin.

 * Consume `POST/PUT/DELETE /api/admin/events` (protegidos por
 * `X-Admin-Token`). La fecha viaja como ISO `YYYY-MM-DD`.
 */

import { useCallback, useEffect, useState } from "react";
import {
  adminCrearEvento,
  adminEditarEvento,
  adminEliminarEvento,
  api,
} from "@/lib/api";
import type { Evento } from "@/lib/types";

type Formulario = {
  nombre: string;
  fecha: string;
  lugar: string;
  ciudad: string;
  artistas: string;
  que_demuestra: string;
};

const VACIO: Formulario = {
  nombre: "",
  fecha: "",
  lugar: "",
  ciudad: "",
  artistas: "",
  que_demuestra: "",
};

type Campo = {
  nombre: keyof Formulario;
  etiqueta: string;
  tipo?: "text" | "date";
  requerido?: boolean;
};

const CAMPOS: Campo[] = [
  { nombre: "nombre", etiqueta: "Nombre", requerido: true },
  { nombre: "fecha", etiqueta: "Fecha", tipo: "date" },
  { nombre: "lugar", etiqueta: "Lugar" },
  { nombre: "ciudad", etiqueta: "Ciudad" },
  { nombre: "artistas", etiqueta: "Cartel (nombres separados por coma)" },
  { nombre: "que_demuestra", etiqueta: "Qué demuestra" },
];

function FormularioEvento({
  inicial,
  onCancelar,
  onGuardar,
}: {
  inicial?: Evento;
  onCancelar?: () => void;
  onGuardar: (valores: EventoBodyPlano) => void;
}) {
  const [form, setForm] = useState<Formulario>(() =>
    inicial
      ? {
          nombre: inicial.nombre,
          fecha: inicial.fecha ?? "",
          lugar: inicial.lugar ?? "",
          ciudad: inicial.ciudad ?? "",
          artistas: inicial.artistas ?? "",
          que_demuestra: inicial.que_demuestra ?? "",
        }
      : VACIO,
  );
  const [guardando, setGuardando] = useState(false);

  return (
    <form
      className="flex flex-col gap-2 rounded-xl border border-line bg-surface p-4"
      onSubmit={async (e) => {
        e.preventDefault();
        setGuardando(true);
        try {
          await onGuardar(form);
        } finally {
          setGuardando(false);
        }
      }}
    >
      <h2 className="font-semibold">
        {inicial ? "Editar evento" : "Nuevo evento"}
      </h2>
      {CAMPOS.map((c) => (
        <input
          key={c.nombre}
          type={c.tipo ?? "text"}
          required={c.requerido}
          value={form[c.nombre]}
          onChange={(e) =>
            setForm((f) => ({ ...f, [c.nombre]: e.target.value }))
          }
          placeholder={c.etiqueta}
          className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
        />
      ))}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={guardando || !form.nombre.trim()}
          className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-bg transition-colors hover:opacity-90 disabled:opacity-50"
        >
          {guardando ? "Guardando…" : inicial ? "Guardar cambios" : "Registrar"}
        </button>
        {onCancelar && (
          <button
            type="button"
            onClick={onCancelar}
            className="rounded-lg border border-line px-3 py-2 text-sm text-muted transition-colors hover:text-text"
          >
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}

type EventoBodyPlano = {
  nombre: string;
  fecha?: string;
  lugar?: string;
  ciudad?: string;
  artistas?: string;
  que_demuestra?: string;
};

export default function PanelEventos({ token }: { token: string }) {
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [cargando, setCargando] = useState(true);
  const [crearNuevo, setCrearNuevo] = useState(false);
  const [editando, setEditando] = useState<number | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      setEventos(await api.eventos());
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar los eventos");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargar();
  }, [cargar]);

  const enviar = async (valores: EventoBodyPlano) => {
    setError("");
    try {
      if (editando !== null) {
        await adminEditarEvento(token, editando, valores);
        setEditando(null);
      } else {
        await adminCrearEvento(token, valores);
        setCrearNuevo(false);
      }
      await cargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo guardar el evento");
    }
  };

  const eliminar = async (e: Evento) => {
    if (!window.confirm(`¿Eliminar el evento «${e.nombre}»?`)) return;
    setError("");
    try {
      await adminEliminarEvento(token, e.id);
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo eliminar el evento");
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-muted">
          {eventos.length} eventos. Un evento nuevo en el cartel de un artista
          cuenta como señal de actividad.
        </p>
        <button
          onClick={() => {
            setCrearNuevo((v) => !v);
            setEditando(null);
          }}
          className="shrink-0 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg hover:opacity-90"
        >
          {crearNuevo ? "Cancelar" : "Nuevo evento"}
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}
      {cargando && <p className="text-sm text-muted">Cargando eventos…</p>}

      {crearNuevo && (
        <FormularioEvento
          onCancelar={() => setCrearNuevo(false)}
          onGuardar={enviar}
        />
      )}

      <div className="flex flex-col gap-2">
        {eventos.map((e) => (
          <div
            key={e.id}
            className="rounded-xl border border-line bg-surface p-3"
          >
            {editando === e.id ? (
              <FormularioEvento
                inicial={e}
                onCancelar={() => setEditando(null)}
                onGuardar={enviar}
              />
            ) : (
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-semibold">{e.nombre}</p>
                  <p className="mt-1 text-xs text-muted">
                    {[e.fecha, e.lugar, e.ciudad].filter(Boolean).join(" · ") ||
                      "Fecha y lugar por confirmar"}
                  </p>
                  {e.artistas && (
                    <p className="mt-1 text-xs text-muted">
                      Cartel: {e.artistas}
                    </p>
                  )}
                  {e.que_demuestra && (
                    <p className="mt-1 text-xs text-muted">{e.que_demuestra}</p>
                  )}
                </div>
                <div className="flex shrink-0 flex-col gap-1">
                  <button
                    onClick={() => {
                      setEditando(e.id);
                      setCrearNuevo(false);
                    }}
                    className="rounded-lg border border-line px-2 py-1 text-xs text-muted transition-colors hover:text-text"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => eliminar(e)}
                    className="rounded-lg border border-line px-2 py-1 text-xs text-red-500 transition-colors hover:bg-red-500/10"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}