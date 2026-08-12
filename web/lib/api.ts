import type { ArtistCard, ArtistDetail, Evento, FeedItem, ResultadoAlta, Stats } from "./types";

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

export const api = {
  artists: () => get<ArtistCard[]>("/api/artists"),
  artist: (slug: string) => get<ArtistDetail>(`/api/artists/${slug}`),
  feed: () => get<FeedItem[]>("/api/feed"),
  eventos: () => get<Evento[]>("/api/events"),
  stats: () => get<Stats>("/api/stats"),
};
