"use client";

/** Acciones de la conexión Meta del perfil: volver a conectar y desconectar.

 * Colapsadas en un enlace discreto "Gestionar Meta" para no molestar al
 * visitante; solo quien busca gestionar el perfil las despliega.
 */

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

export default function ConexionMeta({
  slug,
  conectado,
}: {
  slug: string;
  conectado: boolean;
}) {
  const [abierto, setAbierto] = useState(false);
  const [desconectando, setDesconectando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const prefijo = "#meta_owner=";
    if (window.location.hash.startsWith(prefijo)) {
      localStorage.setItem("fg_meta_owner", window.location.hash.slice(prefijo.length));
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  }, []);

  async function desconectar() {
    setDesconectando(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/feed/igfb/desconectar?slug=${slug}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "X-Meta-Owner": localStorage.getItem("fg_meta_owner") || "",
        },
      });
      if (!res.ok) {
        const datos = await res.json().catch(() => null);
        throw new Error(
          (datos && datos.detail) || "No se pudo desconectar la cuenta",
        );
      }
      window.location.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de conexión");
      setDesconectando(false);
    }
  }

  if (!conectado) {
    return (
      <a
        href={`${API_URL}/api/feed/igfb/login?slug=${slug}`}
        className="mt-1 inline-flex w-36 items-center justify-center gap-2 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg transition-colors hover:opacity-90"
      >
        Conectar Meta
      </a>
    );
  }

  return (
    <div className="inline">
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        className="text-muted underline underline-offset-2 hover:text-text"
      >
        Gestionar Meta
      </button>

      {abierto && (
        <div className="mt-2 flex flex-col items-start gap-2">...
          <a
            href={`${API_URL}/api/feed/igfb/login?slug=${slug}`}
            className="inline-flex w-fit items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-text transition-colors hover:border-accent"
          >
            Volver a conectar
          </a>

          <button
            type="button"
            onClick={desconectar}
            disabled={desconectando}
            className="inline-flex w-fit items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:border-inactivo hover:text-inactivo"
          >
            {desconectando ? "Desconectando..." : "Desconectar"}
          </button>

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )}
    </div>
  );
}
