"use client";

import { useMemo, useState } from "react";
import type { FeedItem } from "@/lib/types";
import FeedCard from "./FeedCard";

export default function FeedLista({ items }: { items: FeedItem[] }) {
  const [q, setQ] = useState("");
  const [tipo, setTipo] = useState("todos");
  const [fuente, setFuente] = useState("todos");
  const [visible, setVisible] = useState(12);

  const tipos = useMemo(
    () => [...new Set(items.map((i) => i.tipo))].sort(),
    [items],
  );
  const fuentes = useMemo(
    () => [...new Set(items.map((i) => i.fuente))].sort(),
    [items],
  );

  const filtrados = useMemo(() => {
    const ql = q.toLowerCase().trim();
    return items.filter((i) => {
      if (tipo !== "todos" && i.tipo !== tipo) return false;
      if (fuente !== "todos" && i.fuente !== fuente) return false;
      if (ql) {
        const texto = `${i.titulo} ${i.artista} ${i.detalle}`.toLowerCase();
        if (!texto.includes(ql)) return false;
      }
      return true;
    });
  }, [items, q, tipo, fuente]);

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setVisible(12);
          }}
          placeholder="Buscar en el feed…"
          className="col-span-2 rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent sm:col-span-2"
        />
        <select
          value={tipo}
          onChange={(e) => {
            setTipo(e.target.value);
            setVisible(12);
          }}
          className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
        >
          <option value="todos">Tipo</option>
          {tipos.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={fuente}
          onChange={(e) => {
            setFuente(e.target.value);
            setVisible(12);
          }}
          className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
        >
          <option value="todos">Fuente</option>
          {fuentes.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
      </div>

      <p className="text-center text-sm text-muted">
        {filtrados.length} publicaciones
      </p>

      {filtrados.length === 0 ? (
        <p className="rounded-xl border border-line bg-surface p-6 text-center text-muted">
          Sin contenido para esos filtros.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {filtrados.slice(0, visible).map((item, i) => (
            <FeedCard key={i} item={item} />
          ))}
          {filtrados.length > visible && (
            <button
              type="button"
              onClick={() => setVisible((v) => v + 12)}
              className="mx-auto rounded-lg border border-line px-4 py-2 text-sm text-muted transition-colors hover:text-text"
            >
              Cargar más
            </button>
          )}
        </div>
      )}
    </div>
  );
}
