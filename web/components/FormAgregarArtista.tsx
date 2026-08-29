"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { crearArtista } from "@/lib/api";
import type { ResultadoAlta } from "@/lib/types";
import {
  FACEBOOK_FRONTERA_GRANDE,
  INSTAGRAM_FRONTERA_GRANDE,
} from "@/lib/contacto";

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

interface RedAgregada {
  plataforma: string;
  url: string;
}

function normalizarCorreo(plataforma: string, url: string): string {
  if (plataforma === "email" && url && !url.toLowerCase().startsWith("mailto:")) {
    return `mailto:${url}`;
  }
  return url;
}

export default function FormAgregarArtista({ onAgregado }: { onAgregado?: () => void }) {
  const [abierto, setAbierto] = useState(false);
  const [nombre, setNombre] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [categoria, setCategoria] = useState<string>("Banda");
  const [generos, setGeneros] = useState("");
  const [bio, setBio] = useState("");
  const [redes, setRedes] = useState<RedAgregada[]>([
    { plataforma: "ig", url: "" },
  ]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creado, setCreado] = useState<ResultadoAlta | null>(null);
  const router = useRouter();

  useEffect(() => {
    function alPresionarTecla(e: KeyboardEvent) {
      if (e.key === "Escape" && abierto && !cargando) {
        setAbierto(false);
        setError(null);
        setCreado(null);
      }
    }
    window.addEventListener("keydown", alPresionarTecla);
    return () => window.removeEventListener("keydown", alPresionarTecla);
  }, [abierto, cargando]);

  useEffect(() => {
    document.body.style.overflow = abierto ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [abierto]);

  function abrir() {
    setAbierto(true);
    setError(null);
    setCreado(null);
  }

  function cerrar() {
    setAbierto(false);
    setError(null);
    setCreado(null);
  }

  function cambiarRed(i: number, campo: keyof RedAgregada, valor: string) {
    setRedes((prev) => prev.map((r, j) => (j === i ? { ...r, [campo]: valor } : r)));
  }

  function quitarRed(i: number) {
    setRedes((prev) => prev.filter((_, j) => j !== i));
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim()) return;
    const redesValidas = redes
      .map((r) => ({
        plataforma: r.plataforma,
        url: normalizarCorreo(r.plataforma, r.url.trim()),
      }))
      .filter((r) => r.url);
    if (redesValidas.length === 0) {
      setError("Incluye al menos un enlace a una red o plataforma.");
      return;
    }
    if (redesValidas.length > 6) {
      setError("Puedes incluir como máximo 6 enlaces.");
      return;
    }
    setCargando(true);
    setError(null);
    try {
      const resultado = await crearArtista({
        nombre: nombre.trim(),
        ciudad: ciudad,
        categoria,
        generos: generos.trim(),
        bio: bio.trim(),
        redes: redesValidas,
      });
      setNombre("");
      setCiudad("");
      setCategoria("Banda");
      setGeneros("");
      setBio("");
      setRedes([{ plataforma: "ig", url: "" }]);
      setCreado(resultado);
      onAgregado?.();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el artista.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <>
      <button
        onClick={abrir}
        className="shrink-0 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg transition-colors hover:opacity-90"
      >
        + Suma tu proyecto
      </button>

      {abierto && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-label="Registro de artista"
          onClick={() => !cargando && cerrar()}
        >
          <div
            className="max-h-[85dvh] w-full max-w-md overflow-y-auto overscroll-contain rounded-2xl border border-line bg-surface p-5 pb-8 fg-scroll-touch"
            onClick={(e) => e.stopPropagation()}
          >
            {creado ? (
              <div className="flex flex-col gap-3">
                <p className="text-sm text-green-600">
                  &quot;{creado.nombre}&quot; registrado ({creado.slug}). El
                  onboarding se ejecutó en el servidor: revisa su perfil.
                </p>
                <p className="text-xs text-amber-500">
                  Conecta tu página de Facebook, Instagram o TikTok desde el
                  perfil para verificar el proyecto. Los proyectos sin verificar
                  pueden ser eliminados.
                </p>
                <div className="flex gap-2">
                  <Link
                    href={`/artistas/${creado.slug}`}
                    onClick={cerrar}
                    className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg transition-colors hover:opacity-90"
                  >
                    Ver perfil
                  </Link>
                  <button
                    type="button"
                    onClick={cerrar}
                    className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted hover:text-text"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={enviar} className="flex flex-col gap-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold">Suma tu proyecto</h2>
                    <p className="text-xs text-muted">
                      Regístrate como artista de la escena de la frontera y
                      completa ahora todos tus datos y enlaces. Después conecta
                      tu página de Facebook o Instagram desde tu perfil para
                      verificarlo y que tus posts se sincronicen
                      automáticamente. También puedes añadir géneros y una bio
                      breve para presentar tu proyecto.
                    </p>
                    <Link
                      href="/ayuda-artistas"
                      className="mt-1 inline-block text-xs text-accent hover:underline"
                    >
                      ¿Necesitas ayuda para conectar tus redes?
                    </Link>
                  </div>
                  <button
                    type="button"
                    onClick={() => !cargando && cerrar()}
                    aria-label="Cerrar"
                    className="shrink-0 rounded-lg border border-line px-2.5 text-sm text-muted hover:text-text"
                  >
                    ×
                  </button>
                </div>

                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Nombre del proyecto *"
                  required
                  className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                />
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={ciudad}
                    onChange={(e) => setCiudad(e.target.value)}
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
                    value={categoria}
                    onChange={(e) => setCategoria(e.target.value)}
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
                  <label htmlFor="generos" className="text-xs text-muted">
                    Géneros (máximo 5, separados por coma)
                  </label>
                  <input
                    id="generos"
                    type="text"
                    value={generos}
                    onChange={(e) => setGeneros(e.target.value)}
                    maxLength={158}
                    placeholder="Ej. Rock, Indie, Alternativo"
                    className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label htmlFor="bio" className="text-xs text-muted">
                    Bio (máximo 500 caracteres)
                  </label>
                  <textarea
                    id="bio"
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    maxLength={500}
                    rows={4}
                    placeholder="Describe brevemente tu proyecto…"
                    className="resize-y rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
                  />
                  <span className="self-end text-xs text-muted">
                    {bio.length}/500
                  </span>
                </div>

                <div className="flex flex-col gap-2">
                  <p className="text-xs text-muted">Redes</p>
                  <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs leading-relaxed text-amber-500">
                    <b>Importante:</b> por ahora, el registro es la única
                    oportunidad de cargar todos tus datos y enlaces. La edición
                    del perfil no está abierta al público todavía, para evitar
                    que alguien malintencionado altere tu ficha; estamos
                    trabajando para que puedas editarla desde tu cuenta. Si
                    necesitas modificar algo de tu proyecto,{" "}
                    <a
                      href={FACEBOOK_FRONTERA_GRANDE}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline underline-offset-2 hover:text-amber-400"
                    >
                      escríbenos por Facebook
                    </a>{" "}
                    o por{" "}
                    <a
                      href={INSTAGRAM_FRONTERA_GRANDE}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline underline-offset-2 hover:text-amber-400"
                    >
                      Instagram de Frontera Grande
                    </a>
                    .
                  </div>
                  <p className="text-xs text-amber-500">
                    Incluye al menos un enlace. Tu proyecto quedará registrado,
                    pero sin verificar.{" "}
                    <b>Los proyectos sin verificar pueden ser eliminados.</b>
                  </p>
                  {redes.map((r, i) => (
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
                      {redes.length > 1 && (
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
                    onClick={() =>
                      setRedes((prev) => [...prev, { plataforma: "ig", url: "" }])
                    }
                    className="w-full rounded-lg border border-dashed border-accent/50 px-3 py-2 text-sm font-medium text-accent transition-colors hover:border-accent hover:bg-accent/10"
                  >
                    + Añadir otra red
                  </button>
                </div>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={cargando}
                    className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg transition-colors hover:opacity-90 disabled:opacity-50"
                  >
                    {cargando ? "Registrando…" : "Registrar proyecto"}
                  </button>
                  <button
                    type="button"
                    onClick={() => !cargando && cerrar()}
                    className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted hover:text-text"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
