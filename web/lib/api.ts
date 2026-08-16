import type { AdminArtist, ArtistCard, ArtistDetail, Evento, FeedItem, ResultadoAlta, Stats } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Error de API ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function crearArtista(body: { nombre: string; ciudad: string; categoria: string; redes: { plataforma: string; url: string }[] }): Promise<ResultadoAlta> {
  const res = await fetch(`${API_URL}/api/artists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const datos = (await res.json()) as ResultadoAlta & { detail?: string };
  if (!res.ok) {
    throw new Error(datos.detail ?? `Error de API ${res.status}`);
  }
  return datos;
}

export async function adminArtistas(token: string): Promise<AdminArtist[]> {
  const res = await fetch(`${API_URL}/api/admin/artists`, {
    headers: { "X-Admin-Token": token },
  });
  const datos = (await res.json()) as AdminArtist[] & { detail?: string };
  if (!res.ok) {
    throw new Error(datos.detail ?? `Error de API ${res.status}`);
  }
  return datos;
}

export async function editarArtista(
  slug: string,
  token: string,
  body: Partial<{
    nombre: string;
    ciudad: string;
    categoria: string;
    generos: string;
    bio: string;
    notas: string;
    logros: string;
    estado_activo: string;
    estado_registro: string;
    redes: { plataforma: string; url: string }[];
  }>,
): Promise<{ ok: boolean; slug: string }> {
  const res = await fetch(`${API_URL}/api/artists/${slug}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": token,
    },
    body: JSON.stringify(body),
  });
  const datos = (await res.json()) as { detail?: string } & { ok?: boolean };
  if (!res.ok) {
    throw new Error(datos.detail ?? `Error de API ${res.status}`);
  }
  return datos as { ok: boolean; slug: string };
}

export async function eliminarArtista(slug: string, token: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/artists/${slug}`, {
    method: "DELETE",
    headers: { "X-Admin-Token": token },
  });
  const datos = (await res.json()) as { detail?: string };
  if (!res.ok) {
    throw new Error(datos.detail ?? `Error de API ${res.status}`);
  }
}

export async function suscribirPush(subscription: PushSubscription): Promise<void> {
  const datos = subscription.toJSON();
  const res = await fetch(`${API_URL}/api/push/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      endpoint: subscription.endpoint,
      keys: datos.keys ?? {},
    }),
  });
  if (!res.ok) throw new Error(`Error de API ${res.status}`);
}

export async function desuscribirPush(endpoint: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/push/unsubscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint, keys: {} }),
  });
  if (!res.ok) throw new Error(`Error de API ${res.status}`);
}

export async function broadcastPush(
  token: string,
  body: { titulo: string; cuerpo: string; url: string },
): Promise<{ enviadas: number }> {
  const res = await fetch(`${API_URL}/api/push/broadcast`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": token,
    },
    body: JSON.stringify(body),
  });
  const datos = (await res.json()) as { enviadas?: number; detail?: string };
  if (!res.ok) throw new Error(datos.detail ?? `Error de API ${res.status}`);
  return { enviadas: datos.enviadas ?? 0 };
}

export const api = {
  artists: () => get<ArtistCard[]>("/api/artists"),
  artist: (slug: string) => get<ArtistDetail>(`/api/artists/${slug}`),
  feed: () => get<FeedItem[]>("/api/feed"),
  eventos: () => get<Evento[]>("/api/events"),
  stats: () => get<Stats>("/api/stats"),
};
