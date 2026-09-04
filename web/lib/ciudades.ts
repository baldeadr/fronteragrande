/** Estados de la escena (región cerrada: Tamaulipas + Valle del Río Grande). */

export type Pais = "MX" | "US";

/**
 * Ciudad base sin sufijo incrustado ni de estado: quita el texto tras la coma
 * ("Roma, Texas" → "Roma") y la abreviatura de lado al final
 * ("Reynosa TM" → "Reynosa", "Hidalgo TX" → "Hidalgo").
 */
export function ciudadBase(ciudad: string | null): string {
  if (!ciudad) return "";
  const prima = ciudad.split(",")[0].trim();
  const limpia = prima.replace(/\s+(?:TM|TX)$/i, "").trim();
  return limpia || prima;
}

/** Ciudad → país, con claves ya normalizadas (minúsculas y sin acentos). */
const PAIS_CIUDAD: Record<string, Pais> = {
  reynosa: "MX",
  matamoros: "MX",
  "rio bravo": "MX",
  camargo: "MX",
  "cd. camargo": "MX",
  "diaz ordaz": "MX",
  mcallen: "US",
  roma: "US",
  laredo: "US",
  edinburg: "US",
  hidalgo: "US",
  "south padre island": "US",
  brownsville: "US",
};

export function paisDeCiudad(ciudad: string | null): Pais | null {
  if (!ciudad) return null;
  const clave = ciudadBase(ciudad)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
  return PAIS_CIUDAD[clave] ?? null;
}

/** Abreviatura corta del estado: TM (Tamaulipas) o TX (Texas). */
const ABREVIATURAS: Record<Pais, string> = {
  MX: "TM",
  US: "TX",
};

export function abreviaturaDeCiudad(ciudad: string | null): string | null {
  if (!ciudad) return null;
  const incrustada = ciudad.trim().match(/\s+(TM|TX)$/i);
  if (incrustada) return incrustada[1].toUpperCase();
  const pais = paisDeCiudad(ciudad);
  return pais ? ABREVIATURAS[pais] : null;
}

/** Etiqueta uniforme: "Ciudad TM"/"Ciudad TX" (todas terminan en el lado). */
export function etiquetaCiudad(ciudad: string | null): string {
  if (!ciudad) return "";
  const base = ciudadBase(ciudad);
  const abrev = abreviaturaDeCiudad(ciudad);
  return abrev ? `${base} ${abrev}` : ciudad;
}