import { ImageResponse } from "@vercel/og";
import type { ArtistDetail } from "@/lib/types";

export const runtime = "edge";
export const alt = "Perfil de artista en Frontera Grande";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const BG = "#0b0b10";
const SURFACE = "#14141b";
const SURFACE2 = "#1b1b24";
const LINE = "#262633";
const TEXT = "#ececf1";
const MUTED = "#8a8a9a";
const ACCENT = "#9d4edd";
const ACCENT_SOFT = "#2a1a33";
const ACTIVO = "#76b041";

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

  const brandFont = "Arial Black, Arial Bold, sans-serif";
  const bodyFont = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: BG,
          color: TEXT,
          padding: 56,
          fontFamily: bodyFont,
        }}
      >
        <div
          style={{
            display: "flex",
            flex: 1,
            borderRadius: 32,
            border: `1px solid ${LINE}`,
            background: `linear-gradient(135deg, ${ACCENT_SOFT} 0%, ${SURFACE} 100%)`,
            padding: 56,
            gap: 48,
            alignItems: "center",
          }}
        >
          {imagen ? (
            <img
              src={imagen}
              alt={nombre}
              width={260}
              height={260}
              style={{
                borderRadius: 28,
                objectFit: "cover",
                border: `4px solid ${LINE}`,
              }}
            />
          ) : (
            <div
              style={{
                width: 260,
                height: 260,
                borderRadius: 28,
                background: SURFACE2,
                border: `4px solid ${LINE}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: brandFont,
                fontSize: 96,
                color: ACCENT,
              }}
            >
              {nombre.charAt(0).toUpperCase()}
            </div>
          )}

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 18,
              flex: 1,
              minWidth: 0,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <span
                style={{
                  fontFamily: brandFont,
                  fontSize: 68,
                  fontWeight: 400,
                  lineHeight: 1.05,
                  color: TEXT,
                  letterSpacing: "-0.02em",
                }}
              >
                {nombre}
              </span>
              {verificado && (
                <span
                  style={{
                    background: ACTIVO,
                    color: BG,
                    fontSize: 20,
                    fontWeight: 700,
                    padding: "8px 16px",
                    borderRadius: 999,
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  Verificado
                </span>
              )}
            </div>

            <span
              style={{
                fontSize: 32,
                color: MUTED,
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
                      background: ACCENT_SOFT,
                      color: ACCENT,
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
            paddingTop: 32,
          }}
        >
          <span
            style={{
              fontFamily: brandFont,
              fontSize: 30,
              fontWeight: 400,
              color: ACCENT,
              letterSpacing: "-0.02em",
            }}
          >
            Frontera Grande
          </span>
          <span
            style={{
              fontSize: 22,
              color: MUTED,
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
