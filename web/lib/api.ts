import type { AdminArtist, ArtistaPendiente, ArtistCard, ArtistDetail, Evento, FeedItem, ResultadoAlta, Stats } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  // Los datos públicos cambian por sincronizaciones, no por cada visita.
  // Mantenerlos unos minutos evita esperar a Render en cada navegación.
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) {
    throw new Error(`Error de API ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function crearArtista(body: { nombre: string; ciudad: string; categoria: string; generos: string; bio: string; redes: { plataforma: string; url: string }[] }): Promise<ResultadoAlta> {
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

export async function adminArtistasPendientes(token: string): Promise<ArtistaPendiente[]> {
  const res = await fetch(`${API_URL}/api/admin/artists/pending`, {
    headers: { "X-Admin-Token": token },
  });
  const datos = (await res.json()) as ArtistaPendiente[] & { detail?: string };
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

export type EventoBody = {
  nombre?: string;
  fecha?: string;
  lugar?: string;
  ciudad?: string;
  artistas?: string;
  que_demuestra?: string;
  fuente?: string;
};

export async function adminCrearEvento(
  token: string,
  body: EventoBody,
): Promise<{ id: number }> {
  const res = await fetch(`${API_URL}/api/admin/events`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": token,
    },
    body: JSON.stringify(body),
  });
  const datos = (await res.json()) as { detail?: string; id?: number };
  if (!res.ok) {
    throw new Error(datos.detail ?? `Error de API ${res.status}`);
  }
  return { id: datos.id ?? 0 };
}

export async function adminEditarEvento(
  token: string,
  id: number,
  body: EventoBody,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/admin/events/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": token,
    },
    body: JSON.stringify(body),
  });
  const datos = (await res.json()) as { detail?: string };
  if (!res.ok) {
    throw new Error(datos.detail ?? `Error de API ${res.status}`);
  }
}

export async function adminEliminarEvento(token: string, id: number): Promise<void> {
  const res = await fetch(`${API_URL}/api/admin/events/${id}`, {
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

export async function adminGetSettings(token: string): Promise<{ notificar_auto_feed: boolean; notificar_auto_verificacion: boolean }> {
  const res = await fetch(`${API_URL}/api/admin/settings`, {
    headers: { "X-Admin-Token": token },
  });
  const datos = (await res.json()) as { detail?: string } & Record<string, unknown>;
  if (!res.ok) throw new Error(datos.detail ?? `Error de API ${res.status}`);
  return datos as { notificar_auto_feed: boolean; notificar_auto_verificacion: boolean };
}

export async function adminPutSettings(
  token: string,
  body: { notificar_auto_feed?: boolean; notificar_auto_verificacion?: boolean },
): Promise<void> {
  const res = await fetch(`${API_URL}/api/admin/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Token": token,
    },
    body: JSON.stringify(body),
  });
  const datos = (await res.json()) as { detail?: string };
  if (!res.ok) throw new Error(datos.detail ?? `Error de API ${res.status}`);
}

export const api = {
  artists: () => get<ArtistCard[]>("/api/artists"),
  artist: (slug: string) => get<ArtistDetail>(`/api/artists/${slug}`),
  feed: () => get<FeedItem[]>("/api/feed"),
  eventos: () => get<Evento[]>("/api/events"),
  stats: () => get<Stats>("/api/stats"),
};

export function buscarArtistas(q: string): Promise<ArtistCard[]> {
  return get<ArtistCard[]>(`/api/artists?q=${encodeURIComponent(q)}`);
}
