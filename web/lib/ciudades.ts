/** Países de las ciudades de la escena (región cerrada: Tamaulipas + Valle del Río Grande). */

export type Pais = "MX" | "US";

/** Ciudad → país, en minúsculas y sin acentos para comparar robusto. */
const PAIS_CIUDAD: Record<string, Pais> = {
  reynosa: "MX",
  matamoros: "MX",
  "río bravo": "MX",
  "cd. camargo": "MX",
  mcallen: "US",
  roma: "US",
  laredo: "US",
  edinburg: "US",
  "south padre island": "US",
  brownsville: "US",
};

export function paisDeCiudad(ciudad: string | null): Pais | null {
  if (!ciudad) return null;
  const clave = ciudad
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
  return PAIS_CIUDAD[clave] ?? null;
}

export function etiquetaCiudad(ciudad: string | null): string {
  if (!ciudad) return "";
  const pais = paisDeCiudad(ciudad);
  if (!pais) return ciudad;
  return pais === "MX" ? `${ciudad}, Tamaulipas` : `${ciudad}, Texas`;
}

const EMOJIS: Record<Pais, string> = {
  MX: "🇲🇽",
  US: "🇺🇸",
};

export function banderaEmoji(pais: Pais | null): string {
  return pais ? EMOJIS[pais] : "";
}