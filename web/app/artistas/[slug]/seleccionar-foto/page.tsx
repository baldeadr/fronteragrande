"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { guardarOwner } from "@/lib/owner";

export default function SeleccionarFotoPage() {
  return (
    <Suspense>
      <SeleccionarFoto />
    </Suspense>
  );
}

function SeleccionarFoto() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = Array.isArray(params.slug) ? params.slug[0] : params.slug;
  const owner = searchParams.get("owner") ?? "";
  const igfb = searchParams.get("igfb");

  const [candidatas, setCandidatas] = useState<Record<string, string>>({});
  const [seleccionada, setSeleccionada] = useState<string | null>(null);
  const [origenSeleccionado, setOrigenSeleccionado] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);

  useEffect(() => {
    if (!owner || !slug) return;
    guardarOwner(slug, owner);
  }, [owner, slug]);

  useEffect(() => {
    if (!owner) return;
    async function cargar() {
      try {
        const res = await fetch(`${API_URL}/api/artists/${slug}`);
        if (!res.ok) throw new Error("No se pudo cargar el artista");
        const data = await res.json();
        if (data.imagen_candidatas) {
          setCandidatas(data.imagen_candidatas);
          const primera = Object.values<string>(data.imagen_candidatas)[0];
          setSeleccionada(primera);
          setOrigenSeleccionado(Object.keys(data.imagen_candidatas)[0]);
        } else if (data.imagen_perfil) {
          setSeleccionada(data.imagen_perfil);
          setOrigenSeleccionado(data.imagen_origen || "actual");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error al cargar");
      } finally {
        setCargando(false);
      }
    }
    cargar();
  }, [slug, owner]);

  if (!owner) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <h1 className="text-2xl font-bold mb-2">Error</h1>
        <p className="text-red-500 mb-6">Sesión de verificación no encontrada. Vuelve a conectar Meta.</p>
        <Link href={`/artistas/${slug}`} className="text-accent underline">
          Volver al perfil
        </Link>
      </div>
    );
  }

  async function guardar() {
    if (!seleccionada || !owner) return;
    setGuardando(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/feed/igfb/${slug}/photo`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Meta-Owner": owner,
        },
        body: JSON.stringify({
          imagen_perfil: seleccionada,
          imagen_origen: origenSeleccionado,
        }),
      });
      if (!res.ok) throw new Error("No se pudo guardar la foto");
      setExito(true);
      setTimeout(() => {
        router.push(`/artistas/${slug}?igfb=ok`);
      }, 1000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setGuardando(false);
    }
  }

  if (cargando) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-accent mx-auto mb-4" />
          <p className="text-muted">Cargando opciones de foto…</p>
        </div>
      </div>
    );
  }

  if (error && !exito) {
    return (
      <div className="max-w-md mx-auto text-center py-12">
        <h1 className="text-2xl font-bold mb-2">Error</h1>
        <p className="text-red-500 mb-6">{error}</p>
        <Link href={`/artistas/${slug}`} className="text-accent underline">
          Volver al perfil
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <div className="mb-6">
        <Link href={`/artistas/${slug}`} className="text-sm text-muted hover:text-text">
          ← Volver al perfil
        </Link>
        <h1 className="mt-2 text-2xl font-bold">Elige tu foto de perfil</h1>
        <p className="mt-1 text-muted">
          Tu perfil se ha verificado con Meta. Elige qué foto mostrar públicamente.
        </p>
      </div>

      {igfb === "ok" && (
        <div className="mb-6 rounded-lg border border-activo/40 bg-activo/10 p-3 text-sm text-activo">
          ✓ Perfil verificado correctamente. Ahora elige tu foto.
        </div>
      )}

      {exito && (
        <div className="mb-6 rounded-lg border border-activo/40 bg-activo/10 p-3 text-sm text-activo">
          ✓ Foto guardada. Redirigiendo a tu perfil…
        </div>
      )}

      {Object.keys(candidatas).length > 0 && (
        <div className="mb-6">
          <h2 className="mb-3 font-semibold">Opciones detectadas</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(candidatas).map(([plataforma, url]) => (
              <label
                key={plataforma}
                className={`flex flex-col items-center gap-2 cursor-pointer rounded-lg border-2 p-3 transition-colors ${
                  seleccionada === url
                    ? "border-accent bg-accent/10"
                    : "border-line hover:border-accent/50"
                }`}
              >
                <input
                  type="radio"
                  name="foto-perfil"
                  value={url}
                  checked={seleccionada === url}
                  onChange={() => {
                    setSeleccionada(url);
                    setOrigenSeleccionado(plataforma);
                  }}
                  className="sr-only"
                />
                <Image
                  src={url}
                  alt={`Candidata ${plataforma}`}
                  width={120}
                  height={120}
                  className="h-28 w-28 object-cover rounded"
                  unoptimized
                />
                <span className="text-xs font-medium text-muted capitalize">{plataforma}</span>
              </label>
            ))}
            <label className="flex flex-col items-center gap-2 cursor-pointer rounded-lg border-2 border-dashed p-3 transition-colors hover:border-accent/50">
              <input
                type="radio"
                name="foto-perfil"
                value="custom"
                checked={
                  origenSeleccionado === "manual" ||
                  (!!seleccionada && !Object.values(candidatas).includes(seleccionada))
                }
                onChange={() => {
                  setSeleccionada("");
                  setOrigenSeleccionado("manual");
                }}
                className="sr-only"
              />
              <div className="h-28 w-28 flex items-center justify-center rounded bg-surface border border-line">
                <span className="text-xs text-muted">URL propia</span>
              </div>
            </label>
          </div>
          {(origenSeleccionado === "manual" ||
            (seleccionada && !Object.values(candidatas).includes(seleccionada))) && (
            <input
              type="url"
              value={seleccionada ?? ""}
              onChange={(e) => setSeleccionada(e.target.value)}
              placeholder="https://…"
              className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
            />
          )}
        </div>
      )}

      {Object.keys(candidatas).length === 0 && (
        <div className="mb-6 rounded-lg border border-line bg-surface p-6 text-center">
          <p className="text-muted mb-4">No se detectaron fotos automáticamente.</p>
          <input
            type="url"
            value={seleccionada ?? ""}
            onChange={(e) => setSeleccionada(e.target.value)}
            placeholder="https://… (URL de tu foto de perfil)"
            className="max-w-md mx-auto rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
          />
        </div>
      )}

      {seleccionada && (
        <div className="flex gap-2">
          <button
            onClick={guardar}
            disabled={guardando}
            className="flex-1 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-bg transition-colors hover:opacity-90 disabled:opacity-50"
          >
            {guardando ? "Guardando…" : "Guardar y continuar"}
          </button>
          <Link
            href={`/artistas/${slug}`}
            className="flex-1 rounded-lg border border-line px-4 py-2 text-sm font-medium text-center text-muted hover:text-text"
          >
            Saltar (usar actual)
          </Link>
        </div>
      )}

      {error && <p className="mt-4 text-sm text-red-500">{error}</p>}
    </div>
  );
}