import { ImageResponse } from "@vercel/og";
import type { ArtistDetail } from "@/lib/types";

export const runtime = "edge";
export const alt = "Perfil de artista en Frontera Grande";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function fetchArtist(slug: string): Promise<ArtistDetail | null> {
  try {
    const res = await fetch(`${API_URL}/api/artists/${slug}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return (await res.json()) as ArtistDetail;
  } catch {
    return null;
  }
}

async function imageToBase64(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const arrayBuffer = await res.arrayBuffer();
    const base64 = Buffer.from(arrayBuffer).toString("base64");
    const contentType = res.headers.get("content-type") ?? "image/png";
    return `data:${contentType};base64,${base64}`;
  } catch {
    return null;
  }
}

export default async function Image({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const artist = await fetchArtist(slug);

  const nombre = artist?.nombre ?? "Frontera Grande";
  const segmento = artist?.segmento ?? "Artista de la escena";
  const ciudad = artist?.ciudad ?? "";
  const generos = artist?.generos?.slice(0, 4) ?? [];
  const rawImagen = artist?.imagen_perfil ?? null;
  const imagen = rawImagen ? await imageToBase64(rawImagen) : null;
  const verificado = artist?.verificado ?? false;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: "linear-gradient(135deg, #0b0b10 0%, #15151f 100%)",
          color: "#f4f4f5",
          padding: 64,
          fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 40,
            flex: 1,
          }}
        >
          {imagen ? (
            <img
              src={imagen}
              alt={nombre}
              width={240}
              height={240}
              style={{
                borderRadius: 24,
                objectFit: "cover",
                border: "4px solid #2a2a35",
              }}
            />
          ) : (
            <div
              style={{
                width: 240,
                height: 240,
                borderRadius: 24,
                background: "#2a2a35",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 80,
                fontWeight: 700,
                color: "#76B041",
              }}
            >
              {nombre.charAt(0).toUpperCase()}
            </div>
          )}

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 16,
              flex: 1,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <span
                style={{
                  fontSize: 64,
                  fontWeight: 800,
                  lineHeight: 1.1,
                  color: "#ffffff",
                }}
              >
                {nombre}
              </span>
              {verificado && (
                <span
                  style={{
                    background: "#76B041",
                    color: "#0b0b10",
                    fontSize: 18,
                    fontWeight: 700,
                    padding: "6px 12px",
                    borderRadius: 999,
                  }}
                >
                  Verificado
                </span>
              )}
            </div>

            <span
              style={{
                fontSize: 32,
                color: "#a1a1aa",
                fontWeight: 500,
              }}
            >
              {segmento}
              {ciudad ? ` · ${ciudad}` : ""}
            </span>

            {generos.length > 0 && (
              <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
                {generos.map((g) => (
                  <span
                    key={g}
                    style={{
                      background: "rgba(118, 176, 65, 0.15)",
                      color: "#76B041",
                      fontSize: 22,
                      fontWeight: 600,
                      padding: "8px 16px",
                      borderRadius: 999,
                    }}
                  >
                    #{g.replace(/\s+/g, "")}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderTop: "1px solid #2a2a35",
            paddingTop: 32,
          }}
        >
          <span
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: "#76B041",
              letterSpacing: "-0.02em",
            }}
          >
            Frontera Grande
          </span>
          <span
            style={{
              fontSize: 22,
              color: "#71717a",
            }}
          >
            Base de datos de la escena musical
          </span>
        </div>
      </div>
    ),
    {
      ...size,
    },
  );
}
