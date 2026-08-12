export const plataformas: Record<
  string,
  { icono: string; nombre: string }
> = {
  ig: { icono: "/assets/icons/dark/instagram.svg", nombre: "Instagram" },
  fb: { icono: "/assets/icons/dark/facebook.svg", nombre: "Facebook" },
  yt: { icono: "/assets/icons/dark/youtube.svg", nombre: "YouTube" },
  tt: { icono: "/assets/icons/dark/tiktok.svg", nombre: "TikTok" },
  spotify: { icono: "/assets/icons/dark/spotify.svg", nombre: "Spotify" },
  bandcamp: { icono: "/assets/icons/dark/bandcamp.svg", nombre: "Bandcamp" },
  soundcloud: {
    icono: "/assets/icons/dark/soundcloud.svg",
    nombre: "SoundCloud",
  },
  apple: { icono: "/assets/icons/dark/applemusic.svg", nombre: "Apple Music" },
  linktree: { icono: "/assets/icons/dark/linktree.svg", nombre: "Linktree" },
  deezer: { icono: "/assets/icons/dark/deezer.svg", nombre: "Deezer" },
  x: { icono: "/assets/icons/dark/x.svg", nombre: "X" },
  web: { icono: "/assets/icons/dark/web.svg", nombre: "Sitio web" },
  otro: { icono: "/assets/icons/dark/otro.svg", nombre: "Otro enlace" },
};

export function infoPlataforma(clave: string) {
  return (
    plataformas[clave] ?? {
      icono: "/assets/icons/dark/escena.svg",
      nombre: clave.toUpperCase(),
    }
  );
}
