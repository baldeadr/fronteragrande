import Link from "next/link";
import Image from "next/image";
import {
  FACEBOOK_FRONTERA_GRANDE,
  INSTAGRAM_FRONTERA_GRANDE,
  SPOTIFY_FRONTERA_GRANDE,
} from "@/lib/contacto";
import Notificaciones from "@/components/Notificaciones";

const redes = [
  {
    href: FACEBOOK_FRONTERA_GRANDE,
    nombre: "Facebook",
    icono: "/assets/icons/dark/facebook.svg",
  },
  {
    href: INSTAGRAM_FRONTERA_GRANDE,
    nombre: "Instagram",
    icono: "/assets/icons/dark/instagram.svg",
  },
  {
    href: SPOTIFY_FRONTERA_GRANDE,
    nombre: "Playlist en Spotify",
    icono: "/assets/icons/dark/spotify.svg",
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-line py-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-1 px-4 text-center text-xs text-muted">
        <p>
          Base de datos interactiva de los proyectos musicales de la frontera
          grande de Tamaulipas.
        </p>
        <p>
          Parte del universo{" "}
          <a
            href="https://baldeadr.github.io/architecting-a-band-web/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            architecting-a-band
          </a>
          .
        </p>
        <nav aria-label="Redes sociales" className="mt-3 flex flex-wrap justify-center gap-2">
          {redes.map((red) => (
            <a
              key={red.nombre}
              href={red.href}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-2 text-text transition-colors hover:border-accent hover:text-accent"
            >
              <Image src={red.icono} alt="" width={16} height={16} aria-hidden />
              <span>{red.nombre}</span>
            </a>
          ))}
        </nav>
        <Link href="/ayuda-artistas" className="text-accent hover:underline">
          Ayuda para artistas
        </Link>
        <Link href="/privacidad" className="text-accent hover:underline">
          Política de privacidad
        </Link>
        <a
          href={FACEBOOK_FRONTERA_GRANDE}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:underline"
        >
          Contacto y correcciones por Facebook
        </a>
        <Link href="/admin" className="text-muted opacity-70 hover:opacity-100 hover:underline">
          Administración
        </Link>
        <Link href="/notificaciones" className="text-accent hover:underline">
          Notificaciones
        </Link>
        <Notificaciones />
      </div>
    </footer>
  );
}
