import { paisDeCiudad, banderaEmoji, type Pais } from "@/lib/ciudades";

/** Banderas de la escena: emoji 🇲🇽/🇺🇸 por defecto; SVGs disponibles para prueba. */

export function BanderaSvg({ pais, className }: { pais: Pais; className?: string }) {
  if (pais === "MX") {
    return (
      <svg viewBox="0 0 3 2" className={className} aria-label="México">
        <rect width="3" height="2" fill="#006847" />
        <rect x="1" width="1" height="2" fill="#ffffff" />
        <rect x="2" width="1" height="2" fill="#ce1126" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 3 2" className={className} aria-label="Estados Unidos">
      <rect width="3" height="2" fill="#ffffff" />
      <rect width="3" height={2 / 13} fill="#b22234" />
      <rect width="3" y={(2 / 13) * 2} height={2 / 13} fill="#b22234" />
      <rect width="3" y={(2 / 13) * 4} height={2 / 13} fill="#b22234" />
      <rect width="3" y={(2 / 13) * 6} height={2 / 13} fill="#b22234" />
      <rect width="3" y={(2 / 13) * 8} height={2 / 13} fill="#b22234" />
      <rect width="3" y={(2 / 13) * 10} height={2 / 13} fill="#b22234" />
      <rect width="3" y={(2 / 13) * 12} height={2 / 13} fill="#b22234" />
      <rect y="0" width={1.12} height={2 / 13 * 7} fill="#3c3b6e" />
    </svg>
  );
}

type Modo = "emoji" | "svg";

export function BanderaCiudad({
  ciudad,
  modo = "emoji",
  className,
}: {
  ciudad: string | null;
  modo?: Modo;
  className?: string;
}) {
  const pais = paisDeCiudad(ciudad);
  if (!pais) return null;
  if (modo === "emoji") {
    return <span className={className}>{banderaEmoji(pais)}</span>;
  }
  return <BanderaSvg pais={pais} className={className} />;
}