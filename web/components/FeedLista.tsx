"use client";

import { useMemo, useState } from "react";
import type { FeedItem } from "@/lib/types";
import FeedCard from "./FeedCard";

export default function FeedLista({ items }: { items: FeedItem[] }) {
  const [q, setQ] = useState("");
  const [visible, setVisible] = useState(12);

  const filtrados = useMemo(() => {
    const ql = q.toLowerCase().trim();
    if (!ql) return items;
    return items.filter((i) => {
      const texto = `${i.titulo} ${i.artista} ${i.detalle}`.toLowerCase();
      return texto.includes(ql);
    });
  }, [items, q]);

  return (
    <div className="flex flex-col gap-5">
      <input
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setVisible(12);
        }}
        placeholder="Buscar en el feed…"
        className="rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
      />

      <p className="text-center text-sm text-muted">
        {filtrados.length} publicaciones
      </p>

      {filtrados.length === 0 ? (
        <p className="rounded-xl border border-line bg-surface p-6 text-center text-muted">
          Sin contenido para ese término.
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