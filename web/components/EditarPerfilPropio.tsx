"use client";

/** Edición de la ficha del propio artista (verificado con Meta).

 * Solo aparece cuando el navegador guarda la sesión de propietario de ese
 * perfil (emitida al verificar vía Meta). Permite editar la información
 * autodescrita: ciudad, categoría, géneros, bio, logros y URLs. El nombre
 * queda fuera (la identidad la decide el administrador) y las estadísticas,
 * nota de curador y estado de actividad se mantienen intactos.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/api";
import { esPropietario, obtenerOwner } from "@/lib/owner";

const CATEGORIAS = ["Banda", "Solista", "DJ", "Colectivo", "Covers", "Tributo"] as const;

const PLATAFORMAS: { valor: string; texto: string }[] = [
  { valor: "ig", texto: "Instagram" },
  { valor: "fb", texto: "Facebook" },
  { valor: "yt", texto: "YouTube" },
  { valor: "tt", texto: "TikTok" },
  { valor: "x", texto: "X (Twitter)" },
  { valor: "spotify", texto: "Spotify" },
  { valor: "bandcamp", texto: "Bandcamp" },
  { valor: "soundcloud", texto: "SoundCloud" },
  { valor: "beatport", texto: "Beatport" },
  { valor: "mixcloud", texto: "Mixcloud" },
  { valor: "apple", texto: "Apple Music" },
  { valor: "linktree", texto: "Linktree" },
  { valor: "email", texto: "Correo electrónico" },
  { valor: "web", texto: "Web" },
  { valor: "otro", texto: "Otra" },
];

const CIUDADES_MX = [
  "Matamoros",
  "Río Bravo",
  "Reynosa",
  "Camargo",
  "Díaz Ordaz",
  "Miguel Alemán",
  "Mier",
  "Guerrero",
  "Nuevo Laredo",
];

const CIUDADES_US = [
  "Laredo",
  "McAllen",
  "Mission",
  "Pharr",
  "Edinburg",
  "Harlingen",
  "Brownsville",
  "Rio Grande City",
  "Roma",
];

interface RedValor {
  plataforma: string;
  url: string;
}

export default function EditarPerfilPropio({
  slug,
  nombre,
  ciudad,
  categoria,
  generos,
  bio,
  logros,
  redes,
}: {
  slug: string;
  nombre: string;
  ciudad: string;
  categoria: string;
  generos: string[];
  bio: string;
  logros: string;
  redes: RedValor[];
}) {
  const router = useRouter();
  const [soyPropietario] = useState(() => esPropietario(slug));
  const [abierto, setAbierto] = useState(false);
  const [valorCiudad, setValorCiudad] = useState(ciudad);
  const [valorCategoria, setValorCategoria] = useState(categoria);
  const [valorGeneros, setValorGeneros] = useState(generos.join(", "));
  const [valorBio, setValorBio] = useState(bio);
  const [valorLogros, setValorLogros] = useState(logros);
  const [valorRedes, setValorRedes] = useState<RedValor[]>(redes);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exito, setExito] = useState(false);

  useEffect(() => {
    function alPresionarTecla(e: KeyboardEvent) {
      if (e.key === "Escape" && abierto) setAbierto(false);
    }
    window.addEventListener("keydown", alPresionarTecla);
    return () => window.removeEventListener("keydown", alPresionarTecla);
  }, [abierto]);

  useEffect(() => {
    document.body.style.overflow = abierto ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [abierto]);

  if (!soyPropietario) {
    return null;
  }

  function cambiarRed(i: number, campo: keyof RedValor, valor: string) {
    setValorRedes((prev) => prev.map((r, j) => (j === i ? { ...r, [campo]: valor } : r)));
  }

  function quitarRed(i: number) {
    setValorRedes((prev) => prev.filter((_, j) => j !== i));
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    const redesValidas = valorRedes.filter((r) => r.url.trim());
    if (redesValidas.length === 0) {
      setError("Incluye al menos un enlace a una red o plataforma.");
      return;
    }
    if (redesValidas.length > 6) {
      setError("Puedes incluir como máximo 6 enlaces.");
      return;
    }
    const ownerToken = obtenerOwner(slug);
    if (!ownerToken) {
      setError("Tu sesión de propietario expiró. Vuelve a conectar tu página desde el perfil.");
      return;
    }
    setCargando(true);
    setError(null);
    setExito(false);
    try {
      const res = await fetch(`${API_URL}/api/feed/igfb/${slug}/perfil`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Meta-Owner": ownerToken,
        },
        body: JSON.stringify({
          ciudad: valorCiudad,
          categoria: valorCategoria,
          generos: valorGeneros.trim(),
          bio: valorBio.trim(),
          logros: valorLogros.trim(),
          redes: redesValidas.map((r) => ({ plataforma: r.plataforma, url: r.url.trim() })),
        }),
      });
      const datos = (await res.json()) as { detail?: string };
      if (!res.ok) {
        throw new Error(datos.detail ?? `Error de API ${res.status}`);
      }
      setExito(true);
      setAbierto(false);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar los cambios.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setAbierto(true);
          setError(null);
          setExito(false);
        }}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:border-accent hover:text-text"
      >
        Editar mi perfil
      </button>

      {abierto && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-label="Editar mi perfil"
          onClick={() => !cargando && setAbierto(false)}
        >
          <div
            className="max-h-[85dvh] w-full max-w-md overflow-y-auto overscroll-contain rounded-2xl border border-line bg-surface p-5 pb-8 fg-scroll-touch"
            onClick={(e) => e.stopPropagation()}
          >
            <form onSubmit={enviar} className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold">Edita tu perfil</h2>
                  <p className="text-xs text-muted">
                    {nombre} — Esta información aparece públicamente en tu
                    ficha. Las estadísticas y el estado de actividad los
                    resuelve el sistema.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => !cargando && setAbierto(false)}
                  aria-label="Cerrar"
                  className="shrink-0 rounded-lg border border-line px-2.5 text-sm text-muted hover:text-text"
                >
                  ×
                </button>
              </div>

              <input
                type="text"
                value={nombre}
                disabled
                title="El nombre lo decide el administrador"
                className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none opacity-60"
              />
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={valorCiudad}
                  onChange={(e) => setValorCiudad(e.target.value)}
                  className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                >
                  <option value="" disabled>
                    Ciudad base…
                  </option>
                  <optgroup label="Tamaulipas">
                    {CIUDADES_MX.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="Valle de Río Grande (EE. UU.)">
                    {CIUDADES_US.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </optgroup>
                  <option value="Otro">Otro</option>
                </select>
                <select
                  value={valorCategoria}
                  onChange={(e) => setValorCategoria(e.target.value)}
                  className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                >
                  {CATEGORIAS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="generos-propios" className="text-xs text-muted">
                  Géneros (máximo 5, separados por coma)
                </label>
                <input
                  id="generos-propios"
                  type="text"
                  value={valorGeneros}
                  onChange={(e) => setValorGeneros(e.target.value)}
                  maxLength={158}
                  placeholder="Ej. Rock, Indie, Alternativo"
                  className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="bio-propia" className="text-xs text-muted">
                  Bio (máximo 500 caracteres)
                </label>
                <textarea
                  id="bio-propia"
                  value={valorBio}
                  onChange={(e) => setValorBio(e.target.value)}
                  maxLength={500}
                  rows={4}
                  placeholder="Describe brevemente tu proyecto…"
                  className="resize-y rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                />
                <span className="self-end text-xs text-muted">{valorBio.length}/500</span>
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="logros-propios" className="text-xs text-muted">
                  Logros (opcional)
                </label>
                <textarea
                  id="logros-propios"
                  value={valorLogros}
                  onChange={(e) => setValorLogros(e.target.value)}
                  rows={2}
                  placeholder="Ej. Gira 2025, sencillo con 100k reproducciones…"
                  className="resize-y rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                />
              </div>

              <div className="flex flex-col gap-2">
                <p className="text-xs text-muted">Redes / dónde escucharte</p>
                <p className="text-xs text-amber-500">
                  Conserva al menos tu página de Facebook (la que usaste para
                  verificar el perfil).
                </p>
                {valorRedes.map((r, i) => (
                  <div key={i} className="flex gap-2">
                    <select
                      value={r.plataforma}
                      onChange={(e) => cambiarRed(i, "plataforma", e.target.value)}
                      className="shrink-0 rounded-lg border border-line bg-surface-2 px-2 py-2 text-sm outline-none focus:border-accent"
                    >
                      {PLATAFORMAS.map((p) => (
                        <option key={p.valor} value={p.valor}>
                          {p.texto}
                        </option>
                      ))}
                    </select>
                    <input
                      type={r.plataforma === "email" ? "email" : "url"}
                      value={r.url}
                      onChange={(e) => cambiarRed(i, "url", e.target.value)}
                      placeholder={r.plataforma === "email" ? "correo@banda.mx" : "https://…"}
                      className="min-w-0 flex-1 rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                    />
                    {valorRedes.length > 1 && (
                      <button
                        type="button"
                        onClick={() => quitarRed(i)}
                        aria-label="Quitar esta red"
                        className="shrink-0 rounded-lg border border-line px-2.5 text-sm text-muted hover:text-text"
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setValorRedes((prev) => [...prev, { plataforma: "ig", url: "" }])}
                  className="self-start text-sm text-muted hover:text-text"
                >
                  + Añadir otra red
                </button>
              </div>

              {error && <p className="text-sm text-red-500">{error}</p>}
              {exito && (
                <p className="text-sm text-green-600">Cambios guardados correctamente.</p>
              )}

              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={cargando}
                  className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg transition-colors hover:opacity-90 disabled:opacity-50"
                >
                  {cargando ? "Guardando…" : "Guardar cambios"}
                </button>
                <button
                  type="button"
                  onClick={() => !cargando && setAbierto(false)}
                  className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted hover:text-text"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
