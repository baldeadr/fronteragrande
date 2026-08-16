"use client";

/** Panel de administración: editar y eliminar perfiles con el token de admin.

 * Pide la clave `ADMIN_PASSWORD` una vez, la guarda en `sessionStorage` y
 * consume `GET /api/admin/artists`, `PUT /api/artists/{slug}` y
 * `DELETE /api/artists/{slug}` (todos protegidos por `X-Admin-Token`).
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  adminArtistas,
  editarArtista,
  eliminarArtista,
} from "@/lib/api";
import type { AdminArtist, LinkAdmin } from "@/lib/types";

const CATEGORIAS = ["Banda", "Solista", "DJ", "Colectivo", "Covers", "Tributo"];

const PLATAFORMAS: { valor: string; texto: string }[] = [
  { valor: "ig", texto: "Instagram" },
  { valor: "fb", texto: "Facebook" },
  { valor: "yt", texto: "YouTube" },
  { valor: "tt", texto: "TikTok" },
  { valor: "spotify", texto: "Spotify" },
  { valor: "bandcamp", texto: "Bandcamp" },
  { valor: "soundcloud", texto: "SoundCloud" },
  { valor: "beatport", texto: "Beatport" },
  { valor: "mixcloud", texto: "Mixcloud" },
  { valor: "apple", texto: "Apple Music" },
  { valor: "linktree", texto: "Linktree" },
  { valor: "deezer", texto: "Deezer" },
  { valor: "web", texto: "Sitio web" },
  { valor: "otro", texto: "Otra" },
];

const ESTADOS_ACTIVO = ["activo", "en_duda", "inactivo"];

const ESTADO_TEXTO: Record<string, string> = {
  activo: "Activo",
  en_duda: "En duda",
  inactivo: "Inactivo",
};

const CLAVE_SESION = "fg_admin_token";

export default function PanelAdmin() {
  const [token, setToken] = useState(() => {
    if (typeof window !== "undefined") {
      return window.sessionStorage.getItem(CLAVE_SESION) ?? "";
    }
    return "";
  });
  const [autenticado, setAutenticado] = useState(false);
  const [artistas, setArtistas] = useState<AdminArtist[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const searchParams = useSearchParams();
  const editarSlug = searchParams.get("editar") ?? "";

  const cargar = useCallback(async (clave: string) => {
    setCargando(true);
    setError("");
    try {
      const datos = await adminArtistas(clave);
      setArtistas(datos);
      setAutenticado(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clave de administrador incorrecta");
      setAutenticado(false);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    // Restaurar sesión al recargar: petición de red al montar.
    const guardada = window.sessionStorage.getItem(CLAVE_SESION);
    if (guardada) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      cargar(guardada);
    }
  }, [cargar]);

  function entrar(e: React.FormEvent) {
    e.preventDefault();
    if (!token.trim()) return;
    window.sessionStorage.setItem(CLAVE_SESION, token.trim());
    cargar(token.trim());
  }

  function salir() {
    window.sessionStorage.removeItem(CLAVE_SESION);
    setToken("");
    setAutenticado(false);
    setArtistas([]);
  }

  if (!autenticado) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold sm:text-3xl">Panel de administración</h1>
        <p className="text-muted">
          Ingresa la clave de administrador para editar o eliminar perfiles.
        </p>
        <form
          onSubmit={entrar}
          className="flex w-full max-w-sm flex-col gap-2"
        >
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Clave de administrador"
            autoFocus
            className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <button
            type="submit"
            disabled={cargando || !token.trim()}
            className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-bg transition-colors hover:opacity-90 disabled:opacity-50"
          >
            {cargando ? "Verificando…" : "Entrar"}
          </button>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </form>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Panel de administración</h1>
          <p className="mt-1 text-muted">
            {artistas.length} perfiles. Pulsa editar para corregir datos o eliminar
            para borrarlo con todo su contenido.
          </p>
        </div>
        <button
          onClick={salir}
          className="shrink-0 rounded-lg border border-line px-3 py-1.5 text-sm text-muted transition-colors hover:text-text"
        >
          Salir
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex flex-col gap-2">
        {artistas.map((a) => (
          <FilaArtista
            key={a.slug}
            artista={a}
            token={token}
            editarInicial={editarSlug === a.slug}
            onGuardado={() => cargar(token)}
          />
        ))}
      </div>
    </div>
  );
}

function FilaArtista({
  artista,
  token,
  onGuardado,
  editarInicial,
}: {
  artista: AdminArtist;
  token: string;
  onGuardado: () => void;
  editarInicial?: boolean;
}) {
  const [editando, setEditando] = useState(Boolean(editarInicial));
  const [confirmando, setConfirmando] = useState(false);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState("");

  async function borrar() {
    setBorrando(true);
    setError("");
    try {
      await eliminarArtista(artista.slug, token);
      onGuardado();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo eliminar");
      setBorrando(false);
    }
  }

  return (
    <div className="rounded-xl border border-line bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="font-medium">
            <Link
              href={`/artistas/${artista.slug}`}
              className="hover:underline"
            >
              {artista.nombre}
            </Link>
            {artista.verificado && (
              <span className="ml-2 text-xs text-accent">✓ Verificado</span>
            )}
          </p>
          <p className="text-xs text-muted">
            {artista.segmento} · {artista.ciudad} ·{" "}
            {ESTADO_TEXTO[artista.estado_activo] ?? artista.estado_activo} ·{" "}
            {artista.estado_registro || "sin estado"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setEditando(true)}
            className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted transition-colors hover:border-accent hover:text-text"
          >
            Editar
          </button>
          {!confirmando ? (
            <button
              onClick={() => setConfirmando(true)}
              className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted transition-colors hover:border-inactivo hover:text-inactivo"
            >
              Eliminar
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">¿Borrar?</span>
              <button
                onClick={borrar}
                disabled={borrando}
                className="rounded-lg bg-inactivo px-3 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {borrando ? "Borrando…" : "Sí, borrar"}
              </button>
              <button
                onClick={() => setConfirmando(false)}
                className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted hover:text-text"
              >
                No
              </button>
            </div>
          )}
        </div>
      </div>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      {editando && (
        <FormEditar
          artista={artista}
          token={token}
          onGuardado={() => {
            setEditando(false);
            onGuardado();
          }}
          onCancelar={() => setEditando(false)}
        />
      )}
    </div>
  );
}

function FormEditar({
  artista,
  token,
  onGuardado,
  onCancelar,
}: {
  artista: AdminArtist;
  token: string;
  onGuardado: () => void;
  onCancelar: () => void;
}) {
  const [nombre, setNombre] = useState(artista.nombre);
  const [ciudad, setCiudad] = useState(artista.ciudad);
  const [categoria, setCategoria] = useState(artista.segmento);
  const [generos, setGeneros] = useState(artista.generos);
  const [estado, setEstado] = useState(artista.estado_activo);
  const [bio, setBio] = useState(artista.bio);
  const [notas, setNotas] = useState(artista.notas);
  const [logros, setLogros] = useState(artista.logros);
  const [redes, setRedes] = useState<LinkAdmin[]>(artista.links.length ? artista.links : [{ plataforma: "ig", url: "" }]);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  function cambiarRed(i: number, campo: keyof LinkAdmin, valor: string) {
    setRedes((prev) => prev.map((r, j) => (j === i ? { ...r, [campo]: valor } : r)));
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    setGuardando(true);
    setError("");
    try {
      await editarArtista(artista.slug, token, {
        nombre: nombre.trim(),
        ciudad: ciudad.trim(),
        categoria,
        generos: generos.trim(),
        estado_activo: estado,
        bio,
        notas,
        logros,
        redes: redes.map((r) => ({ plataforma: r.plataforma, url: r.url.trim() })),
      });
      onGuardado();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
      setGuardando(false);
    }
  }

  return (
    <form
      onSubmit={guardar}
      className="mt-3 flex flex-col gap-3 rounded-lg border border-line bg-surface-2 p-3"
    >
      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Nombre del proyecto"
          required
          className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <select
          value={categoria}
          onChange={(e) => setCategoria(e.target.value)}
          className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
        >
          {CATEGORIAS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={ciudad}
          onChange={(e) => setCiudad(e.target.value)}
          placeholder="Ciudad base"
          className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <input
          type="text"
          value={generos}
          onChange={(e) => setGeneros(e.target.value)}
          placeholder="Géneros (separados por / o ,)"
          className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <select
          value={estado}
          onChange={(e) => setEstado(e.target.value)}
          className="rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
        >
          {ESTADOS_ACTIVO.map((s) => (
            <option key={s} value={s}>
              {ESTADO_TEXTO[s]}
            </option>
          ))}
        </select>
      </div>

      <textarea
        value={bio}
        onChange={(e) => setBio(e.target.value)}
        placeholder="Bio"
        rows={2}
        className="rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
      />
      <textarea
        value={logros}
        onChange={(e) => setLogros(e.target.value)}
        placeholder="Logros"
        rows={2}
        className="rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
      />
      <textarea
        value={notas}
        onChange={(e) => setNotas(e.target.value)}
        placeholder="Notas"
        rows={2}
        className="rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
      />

      <div className="flex flex-col gap-2">
        <p className="text-xs text-muted">Redes (enlaces al puente)</p>
        {redes.map((r, i) => (
          <div key={i} className="flex gap-2">
            <select
              value={r.plataforma}
              onChange={(e) => cambiarRed(i, "plataforma", e.target.value)}
              className="shrink-0 rounded-lg border border-line bg-surface px-2 py-2 text-sm outline-none focus:border-accent"
            >
              {PLATAFORMAS.map((p) => (
                <option key={p.valor} value={p.valor}>
                  {p.texto}
                </option>
              ))}
            </select>
            <input
              type="url"
              value={r.url}
              onChange={(e) => cambiarRed(i, "url", e.target.value)}
              placeholder="https://…"
              className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
            />
            <button
              type="button"
              onClick={() => setRedes((prev) => prev.filter((_, j) => j !== i))}
              aria-label="Quitar esta red"
              className="shrink-0 rounded-lg border border-line px-2.5 text-sm text-muted hover:text-text"
            >
              ×
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => setRedes((prev) => [...prev, { plataforma: "ig", url: "" }])}
          className="self-start text-sm text-muted hover:text-text"
        >
          + Añadir otra red
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={guardando}
          className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-bg transition-colors hover:opacity-90 disabled:opacity-50"
        >
          {guardando ? "Guardando…" : "Guardar cambios"}
        </button>
        <button
          type="button"
          onClick={onCancelar}
          disabled={guardando}
          className="rounded-lg border border-line px-3 py-1.5 text-sm text-muted hover:text-text"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}