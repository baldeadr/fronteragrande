"use client";

import { useEffect, useRef, useState } from "react";

export const PLAYLIST_URL =
  "https://open.spotify.com/playlist/49qIAMVwZCHs5wLo1GLrlz";

function IconoSpotify({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="currentColor"
      aria-hidden
    >
      <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.52 17.34c-.24.36-.66.48-1.02.24-2.82-1.74-6.36-2.1-10.56-1.14-.42.12-.78-.18-.9-.54-.12-.42.18-.78.54-.9 4.56-1.02 8.52-.6 11.64 1.32.42.18.48.66.3 1.02zm1.44-3.3c-.3.42-.84.6-1.26.3-3.24-1.98-8.16-2.58-11.94-1.38-.48.12-1.02-.12-1.14-.6-.12-.48.12-1.02.6-1.14 4.32-1.26 9.72-.6 13.5 1.68.36.18.54.78.24 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.3c-.6.18-1.2-.18-1.38-.72-.18-.6.18-1.2.72-1.38 4.26-1.26 11.28-1.02 15.72 1.62.54.3.72 1.02.42 1.56-.3.42-1.02.6-1.56.3z" />
    </svg>
  );
}

export default function PlaylistSemanal() {
  const [replegada, setReplegada] = useState(true);
  const [saliendo, setSaliendo] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const id = window.setTimeout(() => {
      setReplegada(false);
    }, 4000);
    return () => window.clearTimeout(id);
  }, []);

  function replegar() {
    setSaliendo(true);
    timeoutRef.current = window.setTimeout(() => {
      setReplegada(true);
      setSaliendo(false);
    }, 160);
  }

  function expandir() {
    setSaliendo(true);
    timeoutRef.current = window.setTimeout(() => {
      setReplegada(false);
      setSaliendo(false);
    }, 140);
  }

  if (replegada) {
    return (
      <button
        type="button"
        onClick={expandir}
        aria-label="Abrir la playlist Frontera Grande: Descubrimiento Semanal en Spotify"
        title="Descubrimiento semanal"
        className={`fixed bottom-20 right-1.5 z-40 grid h-11 w-11 place-items-center rounded-full border border-line bg-surface/95 text-text shadow-lg backdrop-blur transition-transform hover:scale-105 hover:border-accent md:bottom-6 md:right-2 ${
          saliendo ? "fg-anim-mini-esconder" : "fg-anim-mini-aparecer"
        }`}
        style={{ right: 6 }}
      >
        <IconoSpotify className="h-5 w-5" />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-20 right-1.5 z-40 md:bottom-6 md:right-2 ${
        saliendo ? "fg-anim-esconder" : "fg-anim-aparecer"
      }`}
      style={{ right: 6 }}
    >
      <a
        href={PLAYLIST_URL}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Abrir la playlist Frontera Grande: Descubrimiento Semanal en Spotify"
        className="group flex items-center gap-1.5 rounded-full border border-line bg-surface/95 py-1 pl-1 pr-2.5 text-xs font-semibold text-text shadow-lg backdrop-blur transition-colors hover:border-accent hover:text-accent"
      >
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-surface-2 text-text transition-colors group-hover:text-accent">
          <IconoSpotify className="h-4 w-4" />
        </span>
        <span className="flex flex-col leading-tight">
          <span>Playlist oficial</span>
          <span className="text-[10px] font-normal text-muted">
            Descubrimiento semanal
          </span>
        </span>
      </a>
      <button
        type="button"
        onClick={replegar}
        aria-label="Ocultar el acceso a la playlist"
        className="absolute grid h-6 w-6 place-items-center rounded-full border border-line bg-bg text-muted shadow transition-colors hover:border-accent hover:text-text"
        style={{ top: -8, right: -8 }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-3.5 w-3.5"
          aria-hidden
        >
          <path d="M6 6l12 12M18 6 6 18" />
        </svg>
      </button>
    </div>
  );
}
