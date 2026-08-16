"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const destinos = [
  { href: "/", texto: "Actividad", icono: "actividad" },
  { href: "/artistas", texto: "Directorio", icono: "directorio" },
  { href: "/eventos", texto: "Eventos", icono: "eventos" },
  { href: "/stats", texto: "Stats", icono: "stats" },
  { href: "/acerca-de", texto: "Acerca", icono: "acerca" },
] as const;

function Icono({ tipo }: { tipo: (typeof destinos)[number]["icono"] }) {
  const props = {
    className: "h-5 w-5",
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
    viewBox: "0 0 24 24",
  };

  if (tipo === "actividad") {
    return <svg {...props}><path d="M4 18V9m5 9V5m5 13v-7m5 7V3" /></svg>;
  }
  if (tipo === "directorio") {
    return <svg {...props}><circle cx="9" cy="8" r="3" /><path d="M3.5 20a5.5 5.5 0 0 1 11 0M16 5.5a3 3 0 0 1 0 5.8M16.5 14.5a5 5 0 0 1 4 5.5" /></svg>;
  }
  if (tipo === "eventos") {
    return <svg {...props}><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4m8-4v4M4 10h16M8 14h3" /></svg>;
  }
  if (tipo === "acerca") {
    return <svg {...props}><circle cx="12" cy="12" r="8" /><path d="M12 11v5m0-8h.01" /></svg>;
  }
  return <svg {...props}><path d="M4 19V5m0 14h16M8 16v-4m4 4V8m4 8V5" /></svg>;
}

function coincideRuta(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function useBarrasOcultas() {
  const [ocultas, setOcultas] = useState(false);

  useEffect(() => {
    let anterior = window.scrollY;

    function alDesplazar() {
      const actual = window.scrollY;
      if (actual < 16) {
        setOcultas(false);
      } else if (Math.abs(actual - anterior) > 8) {
        setOcultas(actual > anterior);
      }
      anterior = actual;
    }

    window.addEventListener("scroll", alDesplazar, { passive: true });
    return () => window.removeEventListener("scroll", alDesplazar);
  }, []);

  return ocultas;
}

export function BotonAtras() {
  const pathname = usePathname();
  const router = useRouter();

  if (pathname === "/") return null;

  return (
    <button
      type="button"
      onClick={() => {
        if (window.history.length > 1) router.back();
        else router.push("/");
      }}
      className="absolute left-3 top-3 grid h-9 w-9 place-items-center rounded-full border border-line bg-surface text-muted transition-colors hover:border-accent hover:text-text md:hidden"
      aria-label="Regresar a la página anterior"
    >
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d="m15 18-6-6 6-6" />
      </svg>
    </button>
  );
}

export default function NavegacionMovil() {
  const pathname = usePathname();
  const ocultas = useBarrasOcultas();

  return (
    <nav
      className={`fixed inset-x-0 bottom-0 z-50 border-t border-line bg-bg/95 px-2 pt-2 backdrop-blur transition-transform duration-200 md:hidden ${ocultas ? "translate-y-full" : "translate-y-0"}`}
      style={{ paddingBottom: "calc(env(safe-area-inset-bottom) + 1.25rem)" }}
      aria-label="Navegación principal"
    >
      <div className="mx-auto flex max-w-lg items-stretch justify-around">
        {destinos.map((destino) => {
          const activo = coincideRuta(pathname, destino.href);
          return (
            <Link
              key={destino.href}
              href={destino.href}
              aria-current={activo ? "page" : undefined}
              className={`flex min-w-0 flex-1 flex-col items-center gap-1 rounded-xl py-1 text-[10px] transition-colors ${
                activo ? "text-accent" : "text-muted hover:text-text"
              }`}
            >
              <Icono tipo={destino.icono} />
              <span>{destino.texto}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
