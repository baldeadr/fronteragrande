export const PLATAFORMA_COLOR: Record<string, string> = {
  ig: "#e1306c",
  fb: "#6e9ff7",
  spotify: "#1db954",
  yt: "#ff5a5a",
  tt: "#36d6d9",
  bandcamp: "#fe9b5a",
  soundcloud: "#f26f5f",
  beatport: "#f65c5c",
  mixcloud: "#52a5e0",
};

export const CATEGORIA_COLOR: Record<string, string> = {
  Banda: "var(--accent)",
  Solista: "#1db954",
  DJ: "#f5a623",
  Colectivo: "#4fa3e8",
  Covers: "#e4572e",
  Tributo: "#b57edc",
};

/** Paleta por índice para la dona de ciudades (el inventario de ciudades cambia). */
export const CIUDAD_PALETA: string[] = [
  "var(--accent)",
  "#1db954",
  "#f5a623",
  "#4fa3e8",
  "#e4572e",
  "#b57edc",
  "#36d6d9",
  "#ff6384",
];

/** Colores de las 4 ligas (Escena incluida), estables para las gráficas por ciudad. */
export const NIVEL_COLOR: Record<string, string> = {
  Escena: "#9d4edd",
  Emergente: "#2fb8a6",
  "Ligas Mayores": "#f5b301",
  "Leyenda de la Frontera": "#aab4c8",
};

/** Paleta estable de los 10 géneros dominantes del catálogo (mismo orden que
 * `lib.helpers.GENEROS_DOMINANTES`), para el desglose de género por ciudad. */
export const GENERO_PALETA: Record<string, string> = {
  Regional: "#4fa3e8",
  Rock: "#e4572e",
  Metal: "#7d9bb5",
  Urbano: "#f5a623",
  EDM: "#36d6d9",
  Dark: "#9d4edd",
  Pop: "#ff6384",
  Cumbia: "#1db954",
  Roots: "#b57edc",
  Experimental: "#f2c94c",
};

export const OTRAS_COLOR = "var(--muted)";
