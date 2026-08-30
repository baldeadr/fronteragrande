import { ImageResponse } from "@vercel/og";
import type { ArtistDetail } from "@/lib/types";
import { ciudadBase } from "@/lib/ciudades";
import { ARCHIVO_BLACK_B64 } from "@/lib/fuente-archivo-black";

export const runtime = "edge";
export const alt = "Perfil de artista en Frontera Grande";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const BG = "#0b0b10";
const SURFACE = "#14141b";
const LINE = "#262633";
const TEXT = "#ececf1";
const MUTED = "#8a8a9a";
const ACCENT = "#9d4edd";
const ACCENT_SOFT = "#2a1a33";

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

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const bin = atob(base64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function IconoVerificado({ size }: { size: number }) {
  // Réplica del IconoVerificado.tsx de la web: círculo morado con paloma.
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      style={{ display: "flex", flexShrink: 0 }}
      fill="none"
    >
      <circle cx="12" cy="12" r="10.5" fill={ACCENT} />
      <path
        d="m7.5 12.2 2.9 2.9 6.1-6.2"
        stroke="#fff"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function Avatar({
  imagen,
  nombre,
}: {
  imagen: string | null;
  nombre: string;
}) {
  // Réplica del Avatar.tsx: círculo con foto o inicial sobre accent-soft.
  if (!imagen) {
    return (
      <div
        style={{
          width: 264,
          height: 264,
          borderRadius: 999,
          background: ACCENT_SOFT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 110,
          fontWeight: 700,
          color: ACCENT,
          flexShrink: 0,
        }}
      >
        {nombre.charAt(0).toUpperCase()}
      </div>
    );
  }
  return (
    <img
      src={imagen}
      alt={nombre}
      width={264}
      height={264}
      style={{
        width: 264,
        height: 264,
        borderRadius: 999,
        objectFit: "cover",
        flexShrink: 0,
      }}
    />
  );
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
  const ciudad = artist?.ciudad ? ciudadBase(artist.ciudad) : "";
  const generos = (artist?.generos ?? []).slice(0, 5);
  const rawImagen = artist?.imagen_perfil ?? null;
  const imagen = rawImagen ? await imageToBase64(rawImagen) : null;
  const verificado = artist?.verificado ?? false;

  const archivoBlack = base64ToArrayBuffer(ARCHIVO_BLACK_B64);

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
          padding: "44px 52px",
          fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            flex: 1,
            borderRadius: 36,
            border: `2px solid ${LINE}`,
            background: `linear-gradient(135deg, ${ACCENT_SOFT} 0%, ${SURFACE} 100%)`,
            padding: "52px 60px",
            alignItems: "center",
            gap: 56,
          }}
        >
          <Avatar imagen={imagen} nombre={nombre} />

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              gap: 22,
              flex: 1,
              minWidth: 0,
            }}
          >
            <span
              style={{
                fontSize: 66,
                fontWeight: 700,
                lineHeight: 1.08,
                letterSpacing: "-0.01em",
              }}
            >
              {nombre}
            </span>

            {verificado && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  marginTop: -8,
                }}
              >
                <IconoVerificado size={38} />
                <span style={{ fontSize: 27, fontWeight: 600, color: MUTED }}>
                  Verificado
                </span>
              </div>
            )}

            <div style={{ display: "flex", fontSize: 31, color: MUTED }}>
              {segmento}
              {ciudad ? ` · ${ciudad}` : ""}
            </div>

            {generos.length > 0 && (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 12,
                  marginTop: 4,
                }}
              >
                {generos.map((g) => (
                  <span
                    key={g}
                    style={{
                      display: "flex",
                      background: ACCENT_SOFT,
                      color: ACCENT,
                      fontSize: 25,
                      fontWeight: 600,
                      padding: "10px 24px",
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
            alignItems: "baseline",
            gap: 16,
            paddingTop: 26,
          }}
        >
          <span
            style={{
              fontFamily: "Archivo Black",
              fontSize: 30,
              color: TEXT,
            }}
          >
            Frontera Grande
          </span>
          <span style={{ fontSize: 24, color: MUTED, display: "flex" }}>
            · fronteragrande.mx
          </span>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        {
          name: "Archivo Black",
          data: archivoBlack,
          style: "normal" as const,
          weight: 400 as const,
        },
      ],
    },
  );
}
