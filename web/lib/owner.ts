/** Sesión del propietario de un perfil (emitida por Meta al verificar).

 * El token `owner` llega por la URL del callback OAuth. Se guarda en
 * `sessionStorage` por slug para que el botón "Editar mi perfil" aparezca
 * solo en el navegador de la persona que verificó el proyecto. Es un token
 * firmado por el backend, válido 30 días; expira al cerrar la pestaña.
 */

const PREFIJO = "fg_owner_";

export function claveOwner(slug: string): string {
  return `${PREFIJO}${slug}`;
}

export function guardarOwner(slug: string, token: string): void {
  if (typeof window === "undefined" || !token) return;
  window.sessionStorage.setItem(claveOwner(slug), token);
}

export function obtenerOwner(slug: string): string {
  if (typeof window === "undefined") return "";
  return window.sessionStorage.getItem(claveOwner(slug)) ?? "";
}

export function esPropietario(slug: string): boolean {
  return Boolean(obtenerOwner(slug));
}
