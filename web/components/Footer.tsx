import Link from "next/link";
import { FACEBOOK_FRONTERA_GRANDE } from "@/lib/contacto";
import Notificaciones from "@/components/Notificaciones";

export default function Footer() {
  return (
    <footer className="border-t border-line py-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-1 px-4 text-center text-xs text-muted">
        <p>
          Base de datos interactiva de los proyectos musicales de la frontera
          grande de Tamaulipas.
        </p>
        <p>
          Parte del universo <span className="text-accent">architecting-a-band</span>.
        </p>
        <Link href="/ayuda-artistas" className="text-accent hover:underline">
          Ayuda para artistas
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
