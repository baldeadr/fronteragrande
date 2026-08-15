import type { MetadataRoute } from "next";
import { api } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://fronteragrande.mx";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const rutasEstaticas: MetadataRoute.Sitemap = [
    { url: BASE, changeFrequency: "daily", priority: 1 },
    { url: `${BASE}/artistas`, changeFrequency: "weekly", priority: 0.9 },
    { url: `${BASE}/eventos`, changeFrequency: "weekly", priority: 0.7 },
    { url: `${BASE}/stats`, changeFrequency: "weekly", priority: 0.5 },
    { url: `${BASE}/ayuda-artistas`, changeFrequency: "monthly", priority: 0.6 },
  ];

  let artistas: MetadataRoute.Sitemap = [];
  try {
    artistas = (await api.artists()).map((a) => ({
      url: `${BASE}/artistas/${a.slug}`,
      changeFrequency: "weekly" as const,
      priority: 0.8,
    }));
  } catch {
    artistas = [];
  }

  return [...rutasEstaticas, ...artistas];
}
