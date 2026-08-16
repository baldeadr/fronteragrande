"use client";

/** Botón de edición visible solo para el administrador con sesión activa.

 * Aparece en el perfil público cuando hay un token de admin en
 * `sessionStorage` y enlaza al panel con el formulario del artista abierto.
 */

import { useState } from "react";
import Link from "next/link";

const CLAVE_SESION = "fg_admin_token";

export default function BotonEditarAdmin({ slug }: { slug: string }) {
  const [esAdmin] = useState(() => {
    if (typeof window !== "undefined") {
      return Boolean(window.sessionStorage.getItem(CLAVE_SESION));
    }
    return false;
  });

  if (!esAdmin) {
    return null;
  }

  return (
    <Link
      href={`/admin?editar=${slug}`}
      className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:border-accent hover:text-text"
    >
      Editar perfil
    </Link>
  );
}