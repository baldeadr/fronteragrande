import { ImageResponse } from "@vercel/og";
import type { Stats } from "@/lib/types";
import { ARCHIVO_BLACK_B64 } from "@/lib/fuente-archivo-black";

export const runtime = "edge";
export const alt = "Frontera Grande — Base de datos de la escena musical";
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

async function fetchStats(): Promise<Stats | null> {
  try {
    const res = await fetch(`${API_URL}/api/stats`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return (await res.json()) as Stats;
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

function Chip({ children }: { children: string }) {
  return (
    <span
      style={{
        display: "flex",
        background: ACCENT_SOFT,
        color: ACCENT,
        fontSize: 28,
        fontWeight: 600,
        padding: "12px 30px",
        borderRadius: 999,
      }}
    >
      {children}
    </span>
  );
}

function Logo({ size }: { size: number }) {
  // Réplica exacta de app/icon.svg: iniciales FG sobre la línea fronteriza.
  return (
    <svg
      viewBox="0 0 512 512"
      width={size}
      height={size}
      style={{ display: "flex" }}
      role="img"
    >
      <rect x="0" y="0" width="512" height="512" rx="78" fill={BG} />
      <path
        d="M 97.28,184.64 H 219.6 v 36.3 h -73.7 v 25.96 h 63.36 v 34.76 H 97.28 Z M 340.13996,182 q 21.78,0 39.16,6.6 17.38,6.6 27.5,19.58 10.34,12.76 10.34,31.24 h -46.42 q 0,-9.46 -8.36,-15.18 -8.36,-5.94 -20.24,-5.94 -17.16,0 -25.96,9.24 -8.8,9.02 -8.8,25.74 v 14.08 q 0,16.72 8.8,25.96 8.8,9.02 25.96,9.02 11.88,0 20.24,-5.5 8.36,-5.72 8.36,-14.52 h -34.32 v -30.8 h 80.74 V 336 h -25.08 l -4.84,-14.96 q -20.68,17.6 -54.12,17.6 -37.62,0 -56.54,-19.58 -18.92,-19.8 -18.92,-58.74 0,-38.5 21.34,-58.3 21.56,-20.02 61.16,-20.02 z"
        fill="#ffffff"
        transform="matrix(0.9,0,0,1.05,25,-45)"
      />
      <path
        d="M80 372h130c14 0 18-18 32-18s18 18 32 18h158"
        fill="none"
        stroke={ACCENT}
        strokeLinecap="round"
        strokeWidth="30"
      />
    </svg>
  );
}

export default async function Image() {
  const stats = await fetchStats();

  const archivoBlack = base64ToArrayBuffer(ARCHIVO_BLACK_B64);

  const chips: string[] = [];
  if (stats) {
    chips.push(`${stats.total} artistas`);
    const ciudades = Object.keys(stats.ciudades ?? {}).length;
    if (ciudades > 0) chips.push(`${ciudades} ciudades`);
    const eventos = stats.eventos_proximos?.total ?? 0;
    if (eventos > 0) chips.push(`${eventos} eventos próximos`);
  }

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
            gap: 30,
          }}
        >
          <Logo size={168} />

          <span
            style={{
              fontFamily: "Archivo Black",
              fontSize: 108,
              lineHeight: 1.05,
              letterSpacing: "-0.01em",
              textAlign: "center",
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

          {chips.length > 0 && (
            <div
              style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 6 }}
            >
              {chips.map((c) => (
                <Chip key={c}>{c}</Chip>
              ))}
            </div>
          )}
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
