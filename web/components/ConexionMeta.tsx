"use client";

/** Acciones de la conexión Meta del perfil: volver a conectar y desconectar.

 * Colapsadas en un enlace discreto "Gestionar Meta" para no molestar al
 * visitante; solo quien busca gestionar el perfil las despliega.
 */

import { useState } from "react";
import { API_URL } from "@/lib/api";

export default function ConexionMeta({
  slug,
  conectado,
}: {
  slug: string;
  conectado: boolean;
}) {
  const [abierto, setAbierto] = useState(false);

  if (!conectado) {
    return (
      <div className="flex flex-col items-start gap-2">
        <button
          type="button"
          disabled
          title="La conexión de Meta está pausada temporalmente"
          className="mt-1 inline-flex w-36 cursor-not-allowed items-center justify-center gap-2 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg opacity-50"
        >
          Conectar Meta
        </button>
        <p className="text-xs text-muted max-w-xs">
          La conexión con Meta está pausada temporalmente. Pronto podrá
          vincular su perfil para verificarlo y recibir visibilidad.
        </p>
      </div>
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
        <div className="mt-2 flex flex-col items-start gap-2">
          <a
            href={`${API_URL}/api/feed/igfb/login?slug=${slug}`}
            className="inline-flex w-fit items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-text transition-colors hover:border-accent"
          >
            Volver a conectar
          </a>

          <a
            href={`${API_URL}/api/feed/igfb/login?slug=${slug}&intencion=desconectar`}
            className="inline-flex w-fit items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:border-inactivo hover:text-inactivo"
          >
            Desconectar
          </a>
        </div>
      )}
    </div>
  );
}