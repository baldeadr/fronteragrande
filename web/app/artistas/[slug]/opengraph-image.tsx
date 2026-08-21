import { ImageResponse } from "@vercel/og";
import type { ArtistDetail } from "@/lib/types";
import { ARCHIVO_BLACK_B64 } from "./fuente-archivo-black";

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

const ETIQUETAS_ESTADO: Record<string, string> = {
  activo: "Activo",
  en_duda: "En duda",
  inactivo: "Inactivo",
};

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

function EstadoBadge({ estado, color }: { estado: string; color: string }) {
  // Réplica del EstadoBadge.tsx de la web: pastilla con punto de color.
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        borderRadius: 999,
        border: `2px solid ${LINE}`,
        background: SURFACE,
        padding: "12px 26px",
        fontSize: 26,
        fontWeight: 500,
        color: TEXT,
      }}
    >
      <span
        style={{
          width: 18,
          height: 18,
          borderRadius: 999,
          background: color,
          display: "flex",
        }}
      />
      {ETIQUETAS_ESTADO[estado] ?? estado}
    </div>
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
  const ciudad = artist?.ciudad ?? "";
  const generos = (artist?.generos ?? []).slice(0, 4);
  const rawImagen = artist?.imagen_perfil ?? null;
  const imagen = rawImagen ? await imageToBase64(rawImagen) : null;
  const verificado = artist?.verificado ?? false;
  const estadoActivo = artist?.estado_activo ?? "";
  const colorEstado = artist?.color_estado ?? "#888888";

  const archivoBlack = base64ToArrayBuffer(ARCHIVO_BLACK_B64);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: BG,
          color: TEXT,
          fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        {imagen ? (
          <img
            src={imagen}
            alt={nombre}
            width={1200}
            height={630}
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        ) : (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: SURFACE2,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 300,
              fontWeight: 700,
              color: ACCENT,
            }}
          >
            {nombre.charAt(0).toUpperCase()}
          </div>
        )}

        <div
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            display: "flex",
            background: imagen
              ? `linear-gradient(to top, ${BG} 0%, ${BG} 30%, rgba(11, 11, 16, 0.72) 55%, rgba(11, 11, 16, 0.15) 80%, rgba(11, 11, 16, 0) 100%)`
              : `linear-gradient(to top, ${BG} 0%, rgba(11, 11, 16, 0.55) 60%, rgba(27, 27, 36, 0.3) 100%)`,
          }}
        />

        {artist && (
          <div style={{ position: "absolute", top: 44, right: 56, display: "flex" }}>
            <EstadoBadge estado={estadoActivo} color={colorEstado} />
          </div>
        )}

        <div
          style={{
            position: "absolute",
            left: 56,
            right: 56,
            bottom: 48,
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            gap: 16,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
            <span
              style={{
                fontSize: 74,
                fontWeight: 700,
                lineHeight: 1.05,
                letterSpacing: "-0.01em",
              }}
            >
              {nombre}
            </span>
            {verificado && <IconoVerificado size={54} />}
          </div>

          <div style={{ fontSize: 32, color: MUTED, display: "flex" }}>
            {segmento}
            {ciudad ? ` · ${ciudad}` : ""}
          </div>

          {generos.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
              {generos.map((g) => (
                <span
                  key={g}
                  style={{
                    display: "flex",
                    background: ACCENT_SOFT,
                    color: ACCENT,
                    fontSize: 25,
                    fontWeight: 600,
                    padding: "8px 22px",
                    borderRadius: 999,
                  }}
                >
                  #{g.replace(/\s+/g, "")}
                </span>
              ))}
            </div>
          )}

          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: 14,
              marginTop: 8,
            }}
          >
            <span
              style={{
                fontFamily: "Archivo Black",
                fontSize: 28,
                color: TEXT,
              }}
            >
              Frontera Grande
            </span>
            <span style={{ fontSize: 23, color: MUTED, display: "flex" }}>
              · fronteragrande.mx · La escena musical de la frontera grande
            </span>
          </div>
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
