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
  const [pedirToken, setPedirToken] = useState(false);
  const [token, setToken] = useState("");

  useEffect(() => {
    const prefijo = "#meta_owner=";
    const parametro = new URLSearchParams(window.location.search).get("owner");
    const fragmento = window.location.hash.startsWith(prefijo)
      ? window.location.hash.slice(prefijo.length)
      : "";
    const token = parametro || fragmento;
    if (token) {
      localStorage.setItem("fg_meta_owner", token);
      window.history.replaceState(null, "", `${window.location.pathname}?igfb=ok`);
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
          ...(token ? { "X-Admin-Token": token } : {}),
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
      setPedirToken(true);
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
            onClick={() => {
              setError("");
              desconectar();
            }}
            disabled={desconectando}
            className="inline-flex w-fit items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:border-inactivo hover:text-inactivo"
          >
            {desconectando ? "Desconectando..." : "Desconectar"}
          </button>

          {pedirToken && (
            <form
              className="flex w-full max-w-md flex-col gap-2 rounded-lg border border-line bg-surface-2 p-3"
              onSubmit={(e) => {
                e.preventDefault();
                desconectar();
              }}
            >
              <label htmlFor="admin-token" className="text-sm text-muted">
                Si la sesión del propietario no está disponible, usa la clave de administrador:
              </label>
              <input
                id="admin-token"
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                autoFocus
                className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-text outline-none focus:border-accent"
              />
              <button
                type="submit"
                disabled={desconectando || !token.trim()}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-inactivo px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                Confirmar con administrador
              </button>
            </form>
          )}

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
      )}
    </div>
  );
}
