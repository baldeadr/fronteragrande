import { ImageResponse } from "@vercel/og";
import { ARCHIVO_BLACK_B64 } from "@/lib/fuente-archivo-black";

export const runtime = "edge";
export const alt = "Frontera Grande — Base de datos de la escena musical";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const BG = "#0b0b10";
const SURFACE = "#14141b";
const LINE = "#262633";
const TEXT = "#ececf1";
const MUTED = "#8a8a9a";
const ACCENT = "#9d4edd";
const ACCENT_SOFT = "#2a1a33";

function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const bin = atob(base64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function Logo({ size }: { size: number }) {
  // Réplica del icono FG: iniciales en Archivo Black sobre la línea
  // fronteriza morada (texto nativo, sin recortes de render).
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.15,
        background: BG,
        border: `2px solid ${LINE}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: size * 0.05,
        flexShrink: 0,
      }}
    >
      <span
        style={{
          fontFamily: "Archivo Black",
          fontSize: size * 0.36,
          lineHeight: 1,
          color: "#ffffff",
          letterSpacing: size * 0.02,
          display: "flex",
        }}
      >
        FG
      </span>
      <svg
        viewBox="60 336 420 62"
        width={size * 0.76}
        height={Math.round((size * 0.76 * 62) / 420)}
        style={{ display: "flex" }}
      >
        <path
          d="M80 372h130c14 0 18-18 32-18s18 18 32 18h158"
          fill="none"
          stroke={ACCENT}
          strokeLinecap="round"
          strokeWidth="30"
        />
      </svg>
    </div>
  );
}

export default async function Image() {
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
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: 36,
            border: `2px solid ${LINE}`,
            background: `linear-gradient(135deg, ${ACCENT_SOFT} 0%, ${SURFACE} 100%)`,
            padding: "48px 60px",
            gap: 26,
          }}
        >
          <Logo size={144} />

          <span
            style={{
              fontFamily: "Archivo Black",
              fontSize: 92,
              lineHeight: 1.05,
              letterSpacing: "-0.01em",
              textAlign: "center",
              display: "flex",
            }}
          >
            Frontera Grande
          </span>

          <span
            style={{
              fontSize: 33,
              color: MUTED,
              textAlign: "center",
              display: "flex",
            }}
          >
            La base de datos de la escena musical de la frontera grande
          </span>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            paddingTop: 26,
          }}
        >
          <span
            style={{
              fontFamily: "Archivo Black",
              fontSize: 26,
              color: MUTED,
            }}
          >
            fronteragrande.mx
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
